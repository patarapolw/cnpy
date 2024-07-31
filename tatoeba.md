```dart
import 'dart:convert';
import 'dart:io';

import 'package:archive/archive_io.dart';
import 'package:http/http.dart';

import 'shared.dart';

const linksFile = 'links.csv';

/// @link https://tatoeba.org/en/downloads
Future downloadTatoeba() async {
  await downloadSentenceTatoeba('cmn');
  await downloadSentenceTatoeba('jpn');
  await downloadSentenceTatoeba('eng');

  await downloadSentenceTatoebaLinks();

  await trimTatoeba();
}

/// Contains all the sentences in the selected language.
/// Each sentence is associated with a unique id and an ISO 639-3 language code.
/// Sentence id `[tab]` Lang `[tab]` Text
///
/// @param lang = cmn, jpn, eng
///
/// @link https://tatoeba.org/en/downloads
Future downloadSentenceTatoeba(String lang) async {
  final downloadFilename = '${lang}_sentences.tsv.bz2';
  final url =
      'https://downloads.tatoeba.org/exports/per_language/$lang/$downloadFilename';
  final zipFile = '$tmpDir/$downloadFilename';

  await File(zipFile).writeAsBytes(await readBytes(Uri.parse(url)));

  final input = InputFileStream(zipFile);
  final output = OutputFileStream('$assetDir/${lang}_sentences.tsv');

  BZip2Decoder().decodeBuffer(input, output: output);

  input.close();
  output.close();
}

/// Contains the links between the sentences.
/// 1 `[tab]` 77 means that sentence #77 is the translation of sentence #1.
/// The reciprocal link is also present, so the file will also contain a line that says 77 `[tab]` 1.
///
/// Filename is [linksFile] ('links.csv')
/// ** Filename extension is originally .csv despite being `[tab]` separated.
///
/// @link https://tatoeba.org/en/downloads
Future downloadSentenceTatoebaLinks() async {
  const downloadFilename = 'links.tar.bz2';
  // const url = 'https://downloads.tatoeba.org/exports/$downloadFilename';
  const zipFile = '$tmpDir/$downloadFilename';

  // await File(zipFile).writeAsBytes(await readBytes(Uri.parse(url)));
  await extractFileToDisk(zipFile, tmpDir);
}

/// [linksFile] is very large. Additionally, 'eng_sentences.tsv' can be trimmed.
Future trimTatoeba() async {
  Set<int> fromLangIds = {};
  Set<int> toLangIds = {};

  Directory(assetDir)
      .listSync()
      .whereType<File>()
      .where((f) => f.uri.pathSegments.last.endsWith('_sentences.tsv'))
      .forEach((f) async {
    final ids = await f
        .openRead()
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .asyncMap((ln) => int.tryParse(ln.split('\t').first))
        .toList();

    if (f.uri.pathSegments.last.startsWith('eng_')) {
      toLangIds.addAll(ids.nonNulls);
    } else {
      fromLangIds.addAll(ids.nonNulls);
    }
  });

  Set<int> engIds = {};

  {
    final inputFile =
        File('$assetDir/$linksFile').renameSync('$tmpDir/$linksFile');
    final outputFile = File('$assetDir/$linksFile').openWrite();

    await inputFile
        .openRead()
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .forEach((ln) {
      final ids = ln
          .split('\t')
          .take(2)
          .map((id) => int.tryParse(id))
          .nonNulls
          .toList(growable: false);
      if (ids.length == 2) {
        if (fromLangIds.contains(ids[0]) && toLangIds.contains(ids[1])) {
          outputFile.writeln('${ids[0]}\t${ids[1]}');
          engIds.add(ids[1]);
        }
      }
    });

    await outputFile.close();
  }

  {
    const engFile = 'eng_sentences.tsv';
    final inputFile = File('$assetDir/$engFile').renameSync('$tmpDir/$engFile');
    final outputFile = File('$assetDir/$engFile').openWrite();

    await inputFile
        .openRead()
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .forEach((ln) {
      final id = int.tryParse(ln.split('\t').first);
      if (id != null && engIds.contains(id)) {
        outputFile.writeln(ln);
      }
    });

    await outputFile.close();
  }
}
```
