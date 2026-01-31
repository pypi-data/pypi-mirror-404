## 1.31.5 - 2026-01-31
### Extractors
#### Additions
- [discord] add `server-search` extractor
- [listal] add `image` & `people` extractors ([#1589](https://github.com/mikf/gallery-dl/issues/1589) [#8921](https://github.com/mikf/gallery-dl/issues/8921))
- [mangafreak] add support ([#8928](https://github.com/mikf/gallery-dl/issues/8928))
- [mangatown] add support ([#8925](https://github.com/mikf/gallery-dl/issues/8925))
- [xenforo] support `titsintops.com` ([#8945](https://github.com/mikf/gallery-dl/issues/8945))
- [xenforo] support `forums.socialmediagirls.com` ([#8964](https://github.com/mikf/gallery-dl/issues/8964))
#### Fixes
- [civitai:user-posts] fix pagination ([#8955](https://github.com/mikf/gallery-dl/issues/8955))
- [imhentai] detect galleries without image data ([#8951](https://github.com/mikf/gallery-dl/issues/8951))
- [kemono] fix possible `AttributeError` when processing revisions ([#8929](https://github.com/mikf/gallery-dl/issues/8929))
- [mangataro] fix `manga` extractor ([#8930](https://github.com/mikf/gallery-dl/issues/8930))
- [pornhub] fix `400 Bad Request` when logged in ([#8942](https://github.com/mikf/gallery-dl/issues/8942))
- [tiktok] solve JS challenges ([#8850](https://github.com/mikf/gallery-dl/issues/8850))
- [tiktok] fix account extraction ([#8931](https://github.com/mikf/gallery-dl/issues/8931))
- [tiktok] extract more story item list pages ([#8932](https://github.com/mikf/gallery-dl/issues/8932))
- [tiktok] do not fail story extraction if a user has no stories ([#8938](https://github.com/mikf/gallery-dl/issues/8938))
- [weebdex] make metadata extraction non-fatal ([#8939](https://github.com/mikf/gallery-dl/issues/8939) [#8954](https://github.com/mikf/gallery-dl/issues/8954))
- [weibo] fix `KeyError - 'pid'` when processing subalbums ([#8792](https://github.com/mikf/gallery-dl/issues/8792))
- [xenforo] improve `attachment` extraction ([#8947](https://github.com/mikf/gallery-dl/issues/8947))
- [xenforo] fix cookies check before login ([#8919](https://github.com/mikf/gallery-dl/issues/8919))
#### Improvements
- [exhentai] implement Multi-Page Viewer support ([#2616](https://github.com/mikf/gallery-dl/issues/2616) [#5268](https://github.com/mikf/gallery-dl/issues/5268))
- [kemono] reduce `revisions` API requests when possible
- [tiktok] implement `subtitles` support ([#8805](https://github.com/mikf/gallery-dl/issues/8805))
- [tiktok] implement downloading all `cover` types ([#8805](https://github.com/mikf/gallery-dl/issues/8805))
- [tiktok] do not stop extraction if a post fails ([#8962](https://github.com/mikf/gallery-dl/issues/8962))
- [weebdex] add `lang` option ([#8957](https://github.com/mikf/gallery-dl/issues/8957))
- [weebdex] support query parameter filters
- [weibo] add `subalbums` include ([#8792](https://github.com/mikf/gallery-dl/issues/8792))
- [xenforo] improve error message extraction ([#8919](https://github.com/mikf/gallery-dl/issues/8919))
- [xenforo] decode `/goto/link-confirmation` links ([#8964](https://github.com/mikf/gallery-dl/issues/8964))
### Post Processors
- [mtime] fix overwriting `Last-Modified` mtime when selecting invalid values ([#8918](https://github.com/mikf/gallery-dl/issues/8918))
### Miscellaneous
- [docs/options] add Table of Contents
- [job] add `output.jsonl` option ([#8953](https://github.com/mikf/gallery-dl/issues/8953))
- [job] add `extractor.*.parent` option
- [job] enable all `parent-…` options for parent extractors by default
