Start with a batch of 20. Will make a new batch if the previous has been surpassed.

After every rounds of not-Right's, there will be unlimited repeat drills until you get everything Right. Additionally, if too many wrongs (10), the repeat drill will start earlier.

No typo checking. However, there is a middle-way button, "Not Sure".

- `ESC` for Not Sure / Skip
- `Ctrl+Z` for undo and redo later (at the end of the queue)
- `F1` or `F5` to end session and start the repeat drill or a new session.
- Mulitple answers if applicable, separated by `;`.
- User vocabularies can be put at `/user/vocab/**/*.txt`, and will be added to Due queue (if the entries exist in [the dictionary](https://www.mdbg.net/chinese/dictionary?page=cc-cedict))
- Skip lists can be put at `/user/skip/**/*.txt`, and will be skipped. For example, if the vocab are accidentally added to the SRS.

![Due Quiz](README/due.png)

![New Quiz](README/new.png)

![Repeat Quiz](README/repeat.png)

## Vocab list ideas

- Hanzi [levels](/assets/zhquiz-vocab.yaml) from [ZhQuiz](https://github.com/zhquiz/level/blob/master/_data/generated/vocab.yaml)

## Stats

Progression stats can be seen in the console. Packaged releases also have the console.

```python
 # zipf frequency according to https://pypi.org/project/wordfreq/, counting only "good"
{'5.x': 217,
 '4.x': 55,
 '3.x': 51,
 '2.x': 4,
 '1.x': 3,
 '0.x': 1,
 # 75th percentile and 99th percentile of the zipf word frequency
 # Random new vocab are given at 0.75 * p75
 'p75': 4.4,
 'p99': 1.77,
 # Vocab with lone or single type of Hanzi
 'lone': '箭匹伞饱矮敲闹灯奶架剑鸟船画坐脸奖入几团求嘛面五信主段越笑金加队线场原手类级水全法指啦年学杀军制连外...',
 'lone.count': 97,
 # Hanzi that repeat in 3 or more vocab. h5 is 5 or more.
 'h3': '不年子大学样好要人么上国为过而对发活行业有然们同中法是偿空台到月入说队女者作在日和什能会最来以怎经进...',
 'h3.count': 51,
 'h5': '不年子大学样好要人么上国为',
 'h5.count': 13,
 # Total vocab count in the SRS (using https://pypi.org/project/fsrs/)
 'studied': 695,
 # fsrs difficulty < 6, e.g. not vocab that were only wrong
 'good': 358,
 # good/studied * 100%
 'accuracy': '51.5%',
 # lone+h3 removed duplicates
 'hanzi.count': 126}
```
