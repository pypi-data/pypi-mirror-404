#!/bin/bash
# Delete XPyCode certificates

CERT_DIR="$HOME/.xpycode/certs"

echo "Deleting XPyCode certificates from: $CERT_DIR"

if [ -d "$CERT_DIR" ]; then
    rm -rf "$CERT_DIR"
    echo "Certificates deleted successfully."
else
    echo "Certificate directory not found: $CERT_DIR"
fi

# Also remove from macOS keychain if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Removing CA certificate from macOS keychain..."
    security delete-certificate -c "XPyCode Development CA" ~/Library/Keychains/login.keychain-db 2>/dev/null || true
fi

echo "Done."
