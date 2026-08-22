{
  "card_id":         "<SUBJ>-M<mod>-<idx>-MAIN-001",
  "card_type":       "STRATEGY",
  "chain_role":      "<BACKGROUND|TRIGGER|PROCESS|RESULT|COUNTER|PATTERN>",
  "maturity":        "RAW",
  "front":           "<30-100字问题，以？结尾>",
  "back_core":       "<150-250字核心答案>",
  "back_detail":     "<800-1200字长文，会升为链article，详尽论述机制/逻辑/案例>",
  "concepts":        ["<概念1>", "<概念2>", "<概念3>", "<概念4>", "<概念5>"],
  "tags":            [
    "#domain/<学科域>",
    "#content/<小主题>",
    "#考频/<★★★|★★|★>",
    "#朝代/<时代|无>"
  ],
  "sources": [
    {
      "type":   "academic",
      "source": "<资料名，如《大气科学》>",
      "detail": "<章节/页码>",
      "url":    ""
    },
    {
      "type":   "textbook",
      "source": "<教材名>",
      "detail": "<章节>",
      "url":    ""
    },
    {
      "type":   "website",
      "source": "<网站名>",
      "detail": "<描述>",
      "url":    "<URL>"
    }
  ],
  "exam_questions": [
    {
      "qid":         "Q1",
      "type":        "单选",
      "question":    "<题干>",
      "options":     ["A <选项>", "B <选项>", "C <选项>", "D <选项>"],
      "answer":      "<答案字母或选项文本>",
      "explanation": "<解析>"
    },
    {
      "qid":         "Q2",
      "type":        "配对",
      "question":    "<匹配题>",
      "options":     ["1-A", "2-B", "3-C", "4-D"],
      "answer":      "<匹配结果>",
      "explanation": "<解析>"
    },
    {
      "qid":         "Q3",
      "type":        "图表排序",
      "question":    "<排序题>",
      "options":     ["①<事件>", "②<事件>", "③<事件>", "④<事件>"],
      "answer":      "<正确顺序，如 ②①④③>",
      "explanation": "<解析>"
    },
    {
      "qid":         "Q4",
      "type":        "材料解析",
      "question":    "<给材料，问问题>",
      "options":     [],
      "answer":      "<答案>",
      "explanation": "<解析>"
    },
    {
      "qid":         "Q5",
      "type":        "开放论述",
      "question":    "<论述题，要求分层给分>",
      "options":     [],
      "answer":      "<答案必含'1~3 <第一层给分> + 4~6 <第二层给分> + 7~8 <第三层给分>'>",
      "explanation": "<解析>"
    }
  ],
  "open_questions": [
    "<存疑1，≤50字>",
    "<存疑2，≤50字>",
    "<存疑3，≤50字>",
    "<存疑4，≤50字>",
    "<存疑5，≤50字>"
  ],
  "confidence":      "<high|medium|low>"
}
