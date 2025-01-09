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
    important_meanings?: string[];
    optional_meanings?: string[];
  };
}

interface State {
  vocabList: IQuizEntry[];
  pendingList: IQuizEntry[];

  vocabDetails: {
    cedict: ICedict[];
    sentences: ISentence[];
    segments: string[];
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

  mode:
    | "old-display"
    | "new-display"
    | "unanswered"
    | "pinyin-answered"
    | "all-answered";
}

declare const ctxmenu: import("../node_modules/ctxmenu/index").CTXMenuSingleton;

declare const showdown: {
  Converter: import("showdown").ConverterStatic;
};
