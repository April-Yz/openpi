#!/bin/bash

THRESHOLD=10   # 百分比阈值
CHECK_INTERVAL=20  # 每20秒检查一次

while true; do
    # 读取 GPU 0 和 1 的显存占用百分比
    GPU0_MEM=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits -i 0 | awk -F',' '{print ($1/$2)*100}')
    GPU1_MEM=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits -i 1 | awk -F',' '{print ($1/$2)*100}')

    echo "GPU0: ${GPU0_MEM}%  GPU1: ${GPU1_MEM}%"

    GPU0_OK=$(echo "$GPU0_MEM < $THRESHOLD" | bc)
    GPU1_OK=$(echo "$GPU1_MEM < $THRESHOLD" | bc)

    if [ "$GPU0_OK" -eq 1 ] && [ "$GPU1_OK" -eq 1 ]; then
        echo "GPU 空闲，启动训练..."
        CUDA_VISIBLE_DEVICES=0,1 XLA_PYTHON_CLIENT_MEM_FRACTION=0.95 uv run scripts/train.py pi05_demospeedup --exp-name=test0212_demospeedup_insertion1
        break
    fi

    echo "GPU 占用高，等待 ${CHECK_INTERVAL}s..."
    sleep $CHECK_INTERVAL
done