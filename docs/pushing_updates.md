# Pushing Updates

## Standard Update (no release)

```bash
git add -A
git commit -m "your message"
git push origin main
```

---

## Update with a Release Tag

```bash
# 1. stage and commit
git add -A
git commit -m "your message"

# 2. create annotated tag with notes
git tag -a v1.1 -m "v1.1 - What changed

- thing 1
- thing 2
- thing 3"

# 3. push code AND tag
git push origin main
git push origin v1.1
```

---

## Delete a Tag (if you messed up)

```bash
# local
git tag -d v1.1

# remote
git push origin --delete v1.1
```

---

## Notes

- `git push origin main` — pushes your code
- `git push origin v1.1` — pushes your tag (version marker)
- Tags don't push automatically, you always have to push them separately
- Use `git tag -a` (annotated) not just `git tag` — annotated tags store your message
