```dart
import 'dart:io';

import 'package:archive/archive_io.dart';
import 'package:http/http.dart';

import 'shared.dart';

/// The basic format of a CC-CEDICT entry is:
/// ```txt
/// Traditional Simplified [pin1 yin1] /gloss; gloss; .../gloss; gloss; .../
/// ```
///
/// For example:
/// ```txt
/// 皮實 皮实 [pi2 shi5] /(of things) durable/(of people) sturdy; tough/
/// ```
///
/// @link https://cc-cedict.org/wiki/format:syntax
///
/// Filename is [cedictFile] ('cedict_ts.u8')
Future downloadCedict() async {
  const fileExt = 'zip';
  // 'https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip'
  // Alternately, 'https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz'
  const url =
      'https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.$fileExt';
  const zipFile = '$tmpDir/cedict.$fileExt';

  await File(zipFile).writeAsBytes(await readBytes(Uri.parse(url)));
  await extractFileToDisk(zipFile, assetDir);
}
```
