#!/bin/bash
if ! command -v node &> /dev/null
then
    echo "NO Node.js"
else
    echo "Node.js OK"
    node -v
    npm install
fi

read -p "按任意键继续..."