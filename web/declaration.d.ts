declare const pywebview: {
  api: {
    log(obj: any): void;
    mark(type: string): Promise<void>;
    vocab_details(v: string): Promise<{
      cedict: ICedict[];
      sentences: ISentence[];
    }>;
    due_vocab_list(): Promise<{
      result: IQuizEntry[];
      count: number;
    }>;
    new_vocab_list(): Promise<{
      result: IQuizEntry[];
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
  };
}
