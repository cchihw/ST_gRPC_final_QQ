#!/bin/bash

SERVER="localhost:50051"
SERVICE="greeter.Greeter"
METHOD="SayHello"

pass() {
  echo "[PASS] $1"
}

fail() {
  echo "[FAIL] $1"
}

test_case() {
  local name="$1"
  local input="$2"
  local expect="$3"

  output=$(grpcurl -plaintext -d "$input" $SERVER $SERVICE/$METHOD 2>&1)
  if echo "$output" | grep -q "$expect"; then
    pass "$name"
  else
    fail "$name"
    echo "  Input:    $input"
    echo "  Expected: $expect"
    echo "  Got:      $output"
  fi
}
# Test cases
test_case "Valid input" '{"name":"Zhi"}' "Hello, Zhi"
test_case "Empty string" '{"name":""}' "Hello"
test_case "Long string" "$(printf '{"name":"%s"}' $(python3 -c 'print("A"*10000)'))" "Hello"
test_case "Unknown field" '{"username":"Zhi"}' "no known field named username"
test_case "Empty JSON" '{}' "Hello"
test_case "Malformed JSON" '{"name": Zhi}' "invalid character 'Z'"


