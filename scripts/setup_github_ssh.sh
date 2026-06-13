#!/bin/bash
# Generate SSH key and print it ready to paste into GitHub

ssh-keygen -t ed25519 -C "dooku-pi" -f ~/.ssh/id_ed25519 -N ""

echo ""
echo "======================================================="
echo " Copy the key below and add it to GitHub:"
echo " github.com → Settings → SSH Keys → New SSH Key"
echo "======================================================="
echo ""
cat ~/.ssh/id_ed25519.pub
echo ""
echo "======================================================="
echo ""
echo "Then run:"
echo "  git remote set-url origin git@github.com:NSM-Barii/dooku.git"
echo "  git push origin main"
