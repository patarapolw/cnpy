declare const pywebview: {
  api: {
    log(obj: any): void;
    open_in_browser(url: string): void;
    mark(v: string, type: string): Promise<void>;
    save_notes(v: string, notes: string): Promise<void>;
    vocab_details(v: string): Promise<{
      cedict: ICedict[];
      sentences: ISentence[];
    }>;
    due_vocab_list(limit?: number): Promise<{
      result: IQuizEntry[];
      count: number;
    }>;
    new_vocab_list(limit?: number): Promise<{
      result: IQuizEntry[];
    }>;
    get_stats(): Promise<{
      lone: string;
      h3: string;
      h5: string;
      good: number;
      accuracy: number;
    }>;
  };
};

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
  };
}

interface State {
  vocabList: IQuizEntry[];
  pendingList: IQuizEntry[];

  vocabDetails: {
    cedict: ICedict[];
    sentences: ISentence[];
  };

  i: number;
  total: number;
  max: number;
  skip: number;
  due: number | "-";

  lastIsRight: boolean | null;
  lastIsFuzzy: boolean;
  lastQuizTime: Date | null;
  isRepeat: boolean;
}
