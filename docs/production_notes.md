# SERVIPLACE production notes

## Media files

Provider images currently use Django local media storage (`MEDIA_ROOT`).

This is enough for local development and early MVP testing, but it is not ideal for long-term production on Render because the default filesystem is ephemeral across deploys.

TODO: when SERVIPLACE starts loading real provider images at scale, move media uploads to Cloudinary, S3, or another persistent object storage provider.

## Static files

Static files are collected with `collectstatic` and served by WhiteNoise in production.

## Recommended start command

```bash
gunicorn config.wsgi:application
```
