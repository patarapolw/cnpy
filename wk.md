---
title: '[App] Hanzi typing SRS with 60 levels and a different studying method'
url: https://community.wanikani.com/t/app-hanzi-typing-srs-with-60-levels-and-a-different-studying-method/69163
---

Also, in search for SRS that works, and so I have deviated from the ways of Anki. I think it can be made to include Japanese, but it's unlikely for me to go that far.

<small> [My old project](https://community.wanikani.com/t/wanikani-for-chinese/43389/4?u=polv) is not online anymore. [[source code](https://github.com/zhquiz/zhquiz)]  </small>

### Features and principles

- Reading only
- Multiple answer input (`;` separated), with options to require multiple important readings
- No real synonyms. Warning shake at best. All answers must exist in the dictionary.
- Typing and auto mark as right/wrong. No changing from wrong-to-right or vice versa.
- Undo (via keyboard shortcut) is sent to the end of review, rather than immediate retyping. Middle button "not sure" is there for half-wrong (Esc shortcut).
- Wrap up every 20 items, but can be done earlier. (F1, and I sometimes wrap-up at 10 items. No need for otherwise decision paralysis.)
- Restudy (drill) wrong items after wrap up.
- Search for inclusive vocabularies, and put studied items first. (Personal preference for hiding reading only if due in 1 hour. Tomorrow or later reviews don't worth hiding reading.)
- Hanzi [break-down](https://github.com/cjkvi/cjkvi-ids) and build-up. Also put studied items first.
- Vocab and Hanzi searching can include reading alongside to narrow the search
- No separating vocab and Hanzi. (Not really an issue for Chinese, but could apply to Japanese.)
- External links and Notes with rich text and images. I encourage taking notes, even if only readings are quizzed.
- Levels, of course. Sorted by language proficiency test levels (HSK), then by most common Hanzi.
- You can start from a mid level. It's just a vocabulary list. Go down level if you feel like it.
- Counting of "known" Hanzi
- Custom vocab list, and custom skip list
- Online text parser

![Hanzi list up|686x500](upload://vVtoeHruN92GJE5yOmml2uWhWOX.png)

## Quizzing

![first time|686x500](upload://ipx7xNVrPVvfHO1jdDiVD38QCWv.png)

![reading select|690x475](upload://tzWDJkGLEXK0haCeRSRDZuf1APT.png)

![repeat|686x500](upload://xJjPONutyJsnerdo0PE3e1d1KRP.png)

Also with history,

![history|690x475](upload://fAGUBe08sCZJwb62LkTcCzarGav.png)

## Levels

![levels|690x411](upload://7HZP1Q3XaYDIQctbcRr2MOPqKXB.jpeg)

## Breakdown

<div align=center>

![sup|510x500](upload://N3r8yOZIc1kZ9ceoYemTrhZZ1v.png)

![including|510x500](upload://j08K7KOQ3BN1lp3fyVVHGTReT27.png)

</div>

## Text analysis

![text analyzer|690x411](upload://zZiO56hzo9rykdxf1CoARjBAwJl.jpeg)

Currently, it's a [desktop app](https://github.com/patarapolw/cnpy/releases), and it's kinda unlikely that I would make it into a website or include Japanese (as it doesn't have much benefit to myself). Anyway, [contributions](https://github.com/patarapolw/cnpy) welcome.

Download the zip file, unzip, and open the exe file.

Also, Happy Chinese New Year :tada: :dragon_face:
