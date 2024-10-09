declare const pywebview: {
  api: {
    log(obj: any): void;
    get_settings(): Promise<Settings>;
    mark(v: string, type: string): Promise<void>;
    save_notes(v: string, notes: string): Promise<void>;
    get_vocab(v: string): Promise<IQuizEntry>;
    set_pinyin(v: string, pinyin: string[] | null): Promise<void>;
    vocab_details(v: string): Promise<{
      cedict: ICedict[];
      sentences: ISentence[];
    }>;
    due_vocab_list(limit?: number): Promise<{
      result: IQuizEntry[];
      count: number;
      new: number;
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
    new_window(
      url: string,
      title: string,
      args?:
        | {
            width: number;
            height: number;
          }
        | { maximized: true }
        | null
    ): Promise<void>;
    load_file(f: string): Promise<string>;
    save_file(f: string, txt: string): Promise<void>;
    update_custom_lists(): Promise<void>;
    get_levels(): Promise<Record<string, string[]>>;
    set_level(lv: number, state: boolean): Promise<void>;
    analyze(txt: string): Promise<{
      result: {
        v: string;
        pinyin: string;
      }[];
    }>;
  };
};

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
