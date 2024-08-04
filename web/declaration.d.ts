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

declare const showdown: {
  Converter: new () => Converter;
};

declare class Converter {
  makeHtml(md: string): string;
  makeMarkdown(html: string): string;
}
