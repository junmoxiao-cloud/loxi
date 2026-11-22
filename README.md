# 龙与孝的中英文单轮评估

Python 3.10 或更高版本，仅使用标准库。默认读取同目录的 protocol.json（当前为待审版本），按冻结时实际采用的提示词更新正文与版本。

1. 用 `python run.py pilot` 或 `python run.py formal` 离线预览6或24个编号与请求内容。
2. 确认供应商、预算、型号、操作者和窗口后复制 config.example.json 为 config.json，填写官方兼容 Chat Completions 地址与设置。通过本地环境变量 MODEL_API_KEY 提供密钥。
3. 用 `python run.py pilot --id P-D-ZH-A-01 --send` 发送单个预试请求。按编号逐条执行。每次请求独立构造，仅传入本题。经预试并登记正式冻结决定后，修改 formal_frozen 和提示版本，再以 formal 执行正式编号。
4. 查看 runs 中请求、服务端返回、结束原因和时间。出现技术失败后先登记异常，再以同编号和 --retry 建立下一次尝试。保留所有响应，首个条件合规的完整回答按台账采用。
5. `python run.py export` 导出各次尝试的 CSV 索引。5号核对编号，再将采用文件相对路径及实际设置登记到实验管理表。机器生成记录不自动构成已审核评分。
