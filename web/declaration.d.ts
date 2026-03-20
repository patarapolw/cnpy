interface Settings {
  levels: number[];
}

interface ICedict {
  simp: string;
  trad?: string;
  pinyin: string;
  english: string[][];
}

interface ISentence {
  id: number;
  cmn: string;
  eng?: string;
}

interface IQuizEntry {
  v: string;
  data: {
    wordfreq: number;
    notes: string;
    pinyin?: string[];
    mustPinyin?: string[];
    warnPinyin?: string[];
  };
}

interface State {
  vocabList: IQuizEntry[];
  pendingList: IQuizEntry[];

  vocabDetails: {
    cedict: ICedict[];
    sentences: ISentence[];
    segments: string[];
    cloze: string | null;
  };

  i: number;
  total: number;
  max: number;
  skip: number;
  due: number;
  new: number;
  review_counter: number;

  lastIsRight: boolean | null;
  lastIsFuzzy: boolean;
  lastQuizTime: Date | null;
  isRepeat: boolean;

  mode?: string;
}

declare const ctxmenu: import("../node_modules/ctxmenu/index").CTXMenuSingleton;

declare const showdown: {
  Converter: import("showdown").ConverterStatic;
};

// Source - https://stackoverflow.com/a/69887283
// Posted by psqli, modified by community. See post 'Timeline' for change history
// Retrieved 2026-03-19, License - CC BY-SA 4.0

interface Promise<T> {
  /** Adds a timeout (in milliseconds) that will reject the promise when expired. */
  withTimeout(milliseconds: number, reason?: string): Promise<T>;
}
