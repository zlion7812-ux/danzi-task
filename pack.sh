#!/bin/bash

OUTPUT_DIR="code_packages"
mkdir -p "$OUTPUT_DIR"

# 打包并标注文件来源
pack_file() {
    local file=$1
    local output=$2
    echo "=========================================" >> "$output"
    echo "=== FILE: $file ===" >> "$output"
    echo "=========================================" >> "$output"
    cat "$file" >> "$output"
    echo -e "\n\n" >> "$output"
}

# 1. 根目录文件
OUTPUT="$OUTPUT_DIR/01_root.txt"
for f in app.py *.json; do
    [ -f "$f" ] && pack_file "$f" "$OUTPUT"
done

# 2. routes 目录
OUTPUT="$OUTPUT_DIR/02_routes.txt"
for f in routes/*.py; do
    [ -f "$f" ] && pack_file "$f" "$OUTPUT"
done

# 3. utils 目录
OUTPUT="$OUTPUT_DIR/03_utils.txt"
for f in utils/*.py; do
    [ -f "$f" ] && pack_file "$f" "$OUTPUT"
done

# 4. templates 目录
OUTPUT="$OUTPUT_DIR/04_templates.txt"
for f in templates/*.html; do
    [ -f "$f" ] && pack_file "$f" "$OUTPUT"
done

echo "打包完成！文件在 $OUTPUT_DIR/ 目录下"
ls -lh $OUTPUT_DIR/
