# 数据说明

## 股票日行情 `stk_daily`

| 列名 | 含义     |
|---------|--------------|
| stk_id   | 股票ID         |
| date   | 日期         |
| open   | 开盘价       |
| high   | 最高价       |
| low    | 最低价       |
| close  | 收盘价       |
| volume | 成交量       |
| amount | 成交额       |
| cumadj | 累积复权因子 |

## 股票财务字段信息映射表 `stk_fin_item_map`

`field`列与财务数据四张表的数据字段一一对应

| 列名 | 含义     |
|---------|--------------|
| item   | 字段名称      |
| table   | 所属财务报表         |
| field   | 对应财务数据字段       |
| english   | 英文名       |
| pinyin    | 拼音       |
| label  | 标签，None or "银行专属" or "保险专属" ...     |

## 股票资产负债表 `stk_fin_balance`

| 列名 | 含义     |
|---------|--------------|
| stk_id   | 股票ID      |
| type   | 公司类型         |
| date   | 数据报告日期       |
| adj   | 代表本条数据为第n次调整/修改后    |
| publish_date    | 发布日期       |
| ...    | 其他，可查询`stk_fin_item_map`表     |

下同

## 股票利润表 `stk_fin_income`

## 股票现金流量表 `stk_fin_cashflow`

## 股票财务报表附注 `stk_fin_annotation`