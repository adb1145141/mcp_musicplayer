from fastmcp import FastMCP
import pandas as pd
import os

mcp = FastMCP("StrictExcelSearch")

DEFAULT_EXCEL_PATH = r"/root/mcp-calculator-main/员工信息登记表.xlsx"


@mcp.tool()
def search_excel_strict(keyword: str) -> dict:
    """
    严格搜索：不猜列、不猜结构
    在整个 Excel 中查找关键词
    """

    if not os.path.exists(DEFAULT_EXCEL_PATH):
        return {"success": False, "error": "Excel 文件不存在"}

    try:
        sheets = pd.read_excel(
            DEFAULT_EXCEL_PATH,
            sheet_name=None,
            header=None,
            dtype=str
        )

        hits = []

        for sheet_name, df in sheets.items():
            df = df.dropna(how="all")

            for row_idx in range(len(df)):
                row = df.iloc[row_idx]

                for col_idx, cell in row.items():
                    if cell and keyword in str(cell):
                        hits.append({
                            "sheet": sheet_name,
                            "row_index": int(row_idx),
                            "column_index": int(col_idx),
                            "matched_cell": cell,
                            "row_data": row.dropna().to_dict()
                        })
                        break  # 一行命中一次即可

        if not hits:
            return {
                "success": True,
                "message": f"未在任何位置找到 {keyword}"
            }

        return {
            "success": True,
            "count": len(hits),
            "result": hits
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
