output=""
expect=""

for i in $(seq 0 100); do
    output=$(cat elliptic_encryption_tests/$i \
        | python elliptic_decryption_pipe.py 2> elliptic_decryption_tests/$i \
        | python elliptic_decryption.py)
    expect=$(tail -n +3 elliptic_encryption_tests/$i)
    if [ "$output" = "$expect" ]; then
        echo ok
    else
        echo fail
    fi
done
