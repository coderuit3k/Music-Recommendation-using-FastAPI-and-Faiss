import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import faiss
import os
from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, JSONResponse
from url import get_youtube_description
from save_results import save_res
import uvicorn

def load_csv(file_path: str) -> pd.DataFrame:
    """
        Loads a CSV file into a pandas DataFrame.

        Args:
            file_path (str): The path to the CSV file.

        Returns:
            pd.DataFrame: The loaded DataFrame.
    """
    music = pd.read_csv(file_path)
    music = music.dropna(axis=0, how="any") # Loại bỏ các hàng có ít nhất một giá trị NaN
    music = music.drop_duplicates(subset=["name"]) # Giữ lại các giá trị (nếu giá trị đó xuất hiện nhiều lần thì chỉ giữ lại 1 lần)
    music = music[["name", "artists", "popularity"]]
    music["summary"] = music["name"].fillna("") + " " + music["artists"].fillna("")
    return music

music = load_csv("universal_top_spotify_songs.csv")

# Vector hóa dữ liệu tổng hợp bằng cách ghép tên bài hát và tên các nghệ sĩ
# Lưu ý: max_features và số lượng music samples phải giống nhau
vectorizer = TfidfVectorizer(stop_words="english", max_features=len(music), ngram_range=(1, 2))
summary_vec = vectorizer.fit_transform(music["summary"]).toarray().astype("float32")

# Lưu trữ các kết quả vector hóa
faiss.normalize_L2(summary_vec)
dim = summary_vec.shape[1]

if os.path.exists("music.index"):
    os.remove("music.index")

index = faiss.IndexFlatIP(dim)
index.add(summary_vec)
faiss.write_index(index, "music.index")

# Tạo class QueryRequest để nhận dữ liệu từ người dùng
class QueryRequest(BaseModel):
    query: str
    top_k: int

# Tạo FastAPI app
app = FastAPI()

@app.post("/search")
def search(req: QueryRequest) -> list:
    """
        Handles search requests and returns the top K results.

        Args:
            req (QueryRequest): The request containing the search query and top K value.

        Returns:
            list: A list of dictionaries containing the search results.
    """
    query_vec = vectorizer.transform([req.query]).toarray().astype('float32')
    faiss.normalize_L2(query_vec)

    scores, indices = index.search(query_vec, req.top_k)

    # Lưu trữ kết quả
    results = []

    try:
        for idx, score in zip(indices[0], scores[0]):
            song = music.iloc[idx]

            video_url, image_url = get_youtube_description(song["name"], song["artists"])

            results.append({
                "name": song["name"],
                "artists": song["artists"],
                "popularity": int(song["popularity"]),
                "video_url": video_url,
                "image_url": image_url
            })

        if not results:
            return HTMLResponse(status_code=404, content={"messages": "Not results found."})

        # Sắp xếp kết quả tìm kiếm dựa trên độ nổi tiếng giảm dần
        results = sorted(results, key=lambda x: x["popularity"], reverse=True)

        # Lưu kết quả thuận tiện cho mỗi lần truy xuất và kiểm tra
        save_res(results, req.query)

        return results
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/images", response_class=HTMLResponse)
def images(names: str = Query(..., description="Comma separated list of music names")):
    names_list = [str(name) for name in names.split(",")]

    html_content = """
    <html>
    <head>
        <title>Search Results</title>
        <style>
            body { font-family: Arial, sans-serif; }
            .item { display: inline-block; margin: 10px; text-align: center; }
            img, iframe { max-width: 300px; border-radius: 10px; }
        </style>
    </head>
    <body>
        <h1>Search Results</h1>
    """

    # Duyệt qua từng thêm bài hát vừa tìm được
    for name in names_list:
        # Duyệt qua DataFrame music lấy ra hàng có tên bài hát trùng với tên bài hát tìm được
        song = music.loc[music["name"] == name].iloc[0]
        video_url, image_url = get_youtube_description(song["name"], song["artists"])

        html_content += f"""
                <div class="item">
                    <h3>{song['name']} - {song['artists']}</h3>
                    <img src="{image_url}" alt="{song['name']}"><br>
                    <iframe width="300" height="169" src= "{video_url}" frameborder="0" allowfullscreen></iframe>
                </div>
                """

    html_content += "</body></html>"

    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)