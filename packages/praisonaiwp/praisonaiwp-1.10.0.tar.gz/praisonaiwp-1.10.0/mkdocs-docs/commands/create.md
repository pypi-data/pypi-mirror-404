# Create Posts

Create WordPress posts with automatic Gutenberg block conversion.

## Basic Usage

```bash
praisonaiwp create "Post Title" --content "<p>Post content here</p>"
```

## Options

| Option | Description |
|--------|-------------|
| `--content TEXT` | Post content (HTML auto-converts to Gutenberg) |
| `--status STATUS` | Post status: draft, publish, pending, private |
| `--type TYPE` | Post type: post, page, or custom type |
| `--category NAME` | Category name or ID |
| `--tags TAGS` | Comma-separated tags |
| `--author USER` | Author username or ID |
| `--date DATE` | Publish date (YYYY-MM-DD HH:MM:SS) |
| `--excerpt TEXT` | Post excerpt |
| `--featured-image PATH` | Set featured image from local file |
| `--no-block-conversion` | Skip HTML to Gutenberg conversion |

## Examples

### Create and Publish

```bash
praisonaiwp create "My Article" \
  --content "<h2>Introduction</h2><p>Welcome to my article.</p>" \
  --status publish \
  --category "Technology"
```

### Create a Page

```bash
praisonaiwp create "About Us" \
  --content "<p>About our company...</p>" \
  --type page \
  --status publish
```

### Create with Tags and Category

```bash
praisonaiwp create "AI News" \
  --content "<p>Latest AI developments...</p>" \
  --category "News" \
  --tags "ai,machine-learning,technology" \
  --status publish
```

### Create Draft for Later

```bash
praisonaiwp create "Draft Post" \
  --content "<p>Work in progress...</p>" \
  --status draft
```

### With Featured Image

```bash
praisonaiwp create "Photo Post" \
  --content "<p>Check out this photo!</p>" \
  --featured-image /path/to/image.jpg \
  --status publish
```

## Gutenberg Block Format

HTML is automatically converted to Gutenberg blocks:

| HTML | Gutenberg Block |
|------|-----------------|
| `<p>text</p>` | `<!-- wp:paragraph -->` |
| `<h2>text</h2>` | `<!-- wp:heading -->` |
| `<ul><li>item</li></ul>` | `<!-- wp:list -->` |
| `<pre>code</pre>` | `<!-- wp:code -->` |
| `<blockquote>text</blockquote>` | `<!-- wp:quote -->` |
| `<table>...</table>` | `<!-- wp:table -->` |

### Raw Gutenberg Blocks

Skip conversion with `--no-block-conversion`:

```bash
praisonaiwp create "Block Post" \
  --no-block-conversion \
  --content '<!-- wp:paragraph --><p>Raw block</p><!-- /wp:paragraph -->'
```

## JSON Output

For scripting:

```bash
praisonaiwp --json create "Post" --content "<p>Hello</p>"
```

Returns:
```json
{
  "success": true,
  "post_id": 123,
  "url": "https://example.com/post/"
}
```

## See Also

- [Update Posts](update.md)
- [List Posts](list.md)
- [Media Upload](media.md)
