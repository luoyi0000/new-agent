#!/usr/bin/env python3
"""图书馆数据种子脚本

从上海图书馆 VuFind API 抓取图书数据、从上海大学图书馆抓取政策文档、
程序化生成座位数据，并构建 ChromaDB 向量索引。

用法:
    python scripts/seed_data.py              # 完整运行
    python scripts/seed_data.py --clear-only  # 仅清空数据
    python scripts/seed_data.py --skip-scrape # 跳过抓取，仅重建索引
"""
import sys
import os
import time
import json
import argparse

# 确保能导入 app 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from bs4 import BeautifulSoup


# =============================================================================
# 第一阶段：清空现有数据
# =============================================================================
def clear_data(db):
    """清空三张表并删除 ChromaDB 集合"""
    print("=" * 60)
    print("清空现有数据...")
    print("=" * 60)

    from app.models.book import Book
    from app.models.policy_doc import PolicyDoc
    from app.models.seat import Seat

    for model in [Book, PolicyDoc, Seat]:
        n = db.query(model).delete()
        print(f"  - 删除 {model.__tablename__}: {n} 条记录")
    db.commit()

    from app.core.chromadb_client import ChromaClient
    chroma = ChromaClient()
    for coll_name in ["library_books", "library_policies"]:
        try:
            chroma.delete_collection(coll_name)
            print(f"  - 删除 ChromaDB 集合: {coll_name}")
        except Exception:
            print(f"  - ChromaDB 集合 {coll_name} 不存在，跳过")
    print()


# =============================================================================
# 第二阶段：图书数据
# =============================================================================
FALLBACK_BOOKS = [
    {"title": "Python编程：从入门到实践", "author": "Eric Matthes", "isbn": "9787115546089", "category": "计算机科学", "description": "本书是一本针对所有层次Python读者而作的Python入门书。全书分两部分：基础知识和项目实践。", "location": "3F-A区-01架"},
    {"title": "流畅的Python", "author": "Luciano Ramalho", "isbn": "9787115455992", "category": "计算机科学", "description": "本书深入探讨了Python语言的高级特性，包括数据模型、序列类型、函数与装饰器等。", "location": "3F-A区-01架"},
    {"title": "机器学习实战：基于Scikit-Learn、Keras和TensorFlow", "author": "Aurelien Geron", "isbn": "9787115547048", "category": "人工智能", "description": "本书通过具体的代码示例，系统地介绍了机器学习的基本概念、算法和最佳实践。", "location": "3F-A区-02架"},
    {"title": "深度学习", "author": "Ian Goodfellow", "isbn": "9787115542845", "category": "人工智能", "description": "深度学习领域的经典教材，由三位世界顶级专家撰写，涵盖了深度学习的理论基础和实践方法。", "location": "3F-A区-02架"},
    {"title": "统计学习方法", "author": "李航", "isbn": "9787302414368", "category": "人工智能", "description": "本书全面系统地介绍了统计学习的主要方法，特别是监督学习方法。", "location": "3F-A区-02架"},
    {"title": "算法导论", "author": "Thomas H. Cormen", "isbn": "9787111407010", "category": "计算机科学", "description": "算法领域的标准教材，全面介绍了各种算法的设计与分析方法。", "location": "3F-A区-03架"},
    {"title": "数据结构与算法分析", "author": "Mark Allen Weiss", "isbn": "9787111539247", "category": "计算机科学", "description": "本书系统介绍了数据结构和算法分析的核心概念，涵盖了常用的数据结构和算法。", "location": "3F-A区-03架"},
    {"title": "深入理解计算机系统", "author": "Randal E. Bryant", "isbn": "9787111544937", "category": "计算机科学", "description": "本书从程序员的视角详细介绍了计算机系统的核心概念。", "location": "3F-A区-04架"},
    {"title": "数据库系统概论", "author": "王珊", "isbn": "9787040406641", "category": "计算机科学", "description": "国内经典数据库教材，系统介绍了数据库系统的基本原理和技术。", "location": "3F-A区-05架"},
    {"title": "三体", "author": "刘慈欣", "isbn": "9787536692930", "category": "文学", "description": "刘慈欣代表作，讲述了地球文明与三体文明的首次接触，中国科幻文学的里程碑之作。", "location": "3F-B区-01架"},
    {"title": "三体II：黑暗森林", "author": "刘慈欣", "isbn": "9787536693944", "category": "文学", "description": "三体系列第二部，展现了宇宙文明间的黑暗森林法则。", "location": "3F-B区-01架"},
    {"title": "三体III：死神永生", "author": "刘慈欣", "isbn": "9787536693968", "category": "文学", "description": "三体系列最终章，揭示了宇宙的终极命运。", "location": "3F-B区-01架"},
    {"title": "百年孤独", "author": "加西亚·马尔克斯", "isbn": "9787544253994", "category": "文学", "description": "魔幻现实主义文学的代表作，讲述了布恩迪亚家族七代人的传奇故事。", "location": "3F-B区-02架"},
    {"title": "活着", "author": "余华", "isbn": "9787506365431", "category": "文学", "description": "讲述了农村人福贵悲惨的人生遭遇，展现了生命的韧性与苦难中的希望。", "location": "3F-B区-02架"},
    {"title": "围城", "author": "钱钟书", "isbn": "9787020024759", "category": "文学", "description": "中国现代文学经典，以幽默讽刺的笔触描绘了知识分子的婚姻与人生困境。", "location": "3F-B区-02架"},
    {"title": "平凡的世界", "author": "路遥", "isbn": "9787530212001", "category": "文学", "description": "全景式地展现了改革开放初期中国城乡社会生活的巨大变迁。", "location": "3F-B区-03架"},
    {"title": "红楼梦", "author": "曹雪芹", "isbn": "9787020002207", "category": "文学", "description": "中国古典四大名著之一，以贾宝玉、林黛玉的爱情悲剧为主线，展现了封建社会的兴衰。", "location": "3F-B区-03架"},
    {"title": "人类简史", "author": "尤瓦尔·赫拉利", "isbn": "9787508660752", "category": "历史", "description": "从认知革命、农业革命到科学革命，探讨了人类历史的重大转折。", "location": "3F-B区-04架"},
    {"title": "未来简史", "author": "尤瓦尔·赫拉利", "isbn": "9787508672069", "category": "历史", "description": "探讨了人工智能和生物技术将如何重塑人类社会的未来。", "location": "3F-B区-04架"},
    {"title": "万历十五年", "author": "黄仁宇", "isbn": "9787108009821", "category": "历史", "description": "以万历十五年为切入点，揭示了明朝政治制度的深层矛盾。", "location": "3F-B区-04架"},
    {"title": "枪炮、病菌与钢铁", "author": "贾雷德·戴蒙德", "isbn": "9787532125849", "category": "历史", "description": "探讨了欧亚大陆文明能够征服其他大陆的根本原因。", "location": "3F-B区-05架"},
    {"title": "国富论", "author": "亚当·斯密", "isbn": "9787100017800", "category": "经济学", "description": "现代经济学的奠基之作，系统阐述了自由市场经济理论。", "location": "3F-C区-01架"},
    {"title": "经济学原理：微观经济学分册", "author": "N.格里高利·曼昆", "isbn": "9787301256909", "category": "经济学", "description": "全球最受欢迎的经济学入门教材，以通俗易懂的语言阐释经济学基本原理。", "location": "3F-C区-01架"},
    {"title": "经济学原理：宏观经济学分册", "author": "N.格里高利·曼昆", "isbn": "9787301256916", "category": "经济学", "description": "宏观经济学的经典入门教材，涵盖国民收入、通货膨胀、失业等核心议题。", "location": "3F-C区-01架"},
    {"title": "思考，快与慢", "author": "丹尼尔·卡尼曼", "isbn": "9787508633558", "category": "心理学", "description": "诺贝尔经济学奖得主卡尼曼揭示了人类思维的两个系统及其对决策的影响。", "location": "3F-C区-02架"},
    {"title": "自卑与超越", "author": "阿尔弗雷德·阿德勒", "isbn": "9787569903799", "category": "心理学", "description": "个体心理学创始人阿德勒的经典之作，探讨了自卑感如何驱动人类行为。", "location": "3F-C区-02架"},
    {"title": "梦的解析", "author": "西格蒙德·弗洛伊德", "isbn": "9787532765847", "category": "心理学", "description": "精神分析学派的奠基之作，系统阐述了梦的机制和意义。", "location": "3F-C区-02架"},
    {"title": "社会心理学", "author": "戴维·迈尔斯", "isbn": "9787115206406", "category": "心理学", "description": "社会心理学领域的权威教材，全面介绍了社会思维、社会影响和社会关系。", "location": "3F-C区-03架"},
    {"title": "设计中的设计", "author": "原研哉", "isbn": "9787807461487", "category": "设计", "description": "日本设计大师原研哉对设计本质的深入思考，探讨了设计与日常生活的关系。", "location": "4F-A区-01架"},
    {"title": "写给大家看的设计书", "author": "Robin Williams", "isbn": "9787115336455", "category": "设计", "description": "以简洁明了的方式介绍了设计的基本原则：亲密性、对齐、重复和对比。", "location": "4F-A区-01架"},
    {"title": "摄影笔记", "author": "宁思潇潇", "isbn": "9787115478083", "category": "摄影", "description": "一本通俗易懂的摄影入门书，从相机操作到构图技巧，带你走进摄影的世界。", "location": "4F-A区-03架"},
    {"title": "美的历程", "author": "李泽厚", "isbn": "9787108041098", "category": "哲学", "description": "中国美学的经典之作，从远古到明清，勾勒了中国审美意识的演变历程。", "location": "4F-B区-01架"},
    {"title": "论语译注", "author": "杨伯峻", "isbn": "9787101100213", "category": "哲学", "description": "《论语》的权威译注本，对孔子及其弟子的言行进行了详尽的注解和翻译。", "location": "4F-B区-01架"},
    {"title": "纯粹理性批判", "author": "伊曼努尔·康德", "isbn": "9787100004848", "category": "哲学", "description": "西方哲学史上最重要的著作之一，探讨了人类理性的界限和先天认识形式。", "location": "4F-B区-02架"},
    {"title": "存在与时间", "author": "马丁·海德格尔", "isbn": "9787100015837", "category": "哲学", "description": "存在主义哲学的奠基之作，重新提出了存在的根本性哲学问题。", "location": "4F-B区-02架"},
    {"title": "时间简史", "author": "斯蒂芬·霍金", "isbn": "9787544344289", "category": "物理学", "description": "霍金的经典科普著作，以通俗的语言介绍了宇宙的起源、黑洞和时间旅行。", "location": "4F-C区-01架"},
    {"title": "上帝掷骰子吗", "author": "曹天元", "isbn": "9787559630612", "category": "物理学", "description": "用生动有趣的笔触讲述了量子力学的历史和发展，中国最畅销的科普读物之一。", "location": "4F-C区-01架"},
    {"title": "物种起源", "author": "查尔斯·达尔文", "isbn": "9787532832280", "category": "生物学", "description": "进化论的奠基之作，提出了自然选择学说，彻底改变了人类对生命起源的认识。", "location": "4F-C区-02架"},
    {"title": "自私的基因", "author": "理查德·道金斯", "isbn": "9787508660158", "category": "生物学", "description": "以基因为中心的进化论视角，揭示了生物行为的根本动因。", "location": "4F-C区-02架"},
    {"title": "大数据时代", "author": "维克托·迈尔-舍恩伯格", "isbn": "9787549522104", "category": "大数据", "description": "大数据思维变革的启蒙之作，阐述了大数据如何改变我们的生活、工作和思维。", "location": "5F-A区-01架"},
    {"title": "利用Python进行数据分析", "author": "Wes McKinney", "isbn": "9787115543484", "category": "大数据", "description": "Python数据分析的权威指南，详细介绍了pandas、NumPy等库的使用。", "location": "5F-A区-01架"},
    {"title": "机器学习", "author": "周志华", "isbn": "9787302423285", "category": "人工智能", "description": "国内机器学习领域的经典教材，系统介绍了机器学习的基本理论与算法。", "location": "5F-A区-02架"},
    {"title": "算法图解", "author": "Aditya Bhargava", "isbn": "9787115447638", "category": "计算机科学", "description": "以图解的方式生动介绍了常用算法，适合算法入门读者。", "location": "5F-B区-01架"},
    {"title": "程序员修炼之道", "author": "Andrew Hunt", "isbn": "9787121028294", "category": "计算机科学", "description": "软件开发领域的经典之作，涵盖了编程实践、项目管理和职业发展的智慧。", "location": "5F-B区-01架"},
    {"title": "重构：改善既有代码的设计", "author": "Martin Fowler", "isbn": "9787111551829", "category": "计算机科学", "description": "重构技术的权威指南，详细介绍了改善代码结构的方法和模式。", "location": "5F-B区-01架"},
    {"title": "代码整洁之道", "author": "Robert C. Martin", "isbn": "9787115216870", "category": "计算机科学", "description": "敏捷开发大师Martin阐述了编写整洁代码的原则、模式和实践。", "location": "5F-B区-02架"},
    {"title": "人月神话", "author": "Frederick P. Brooks Jr.", "isbn": "9787302140649", "category": "计算机科学", "description": "软件工程领域的经典之作，关于大型软件开发项目管理的深刻洞见。", "location": "5F-B区-02架"},
    {"title": "黑客与画家", "author": "Paul Graham", "isbn": "9787115249496", "category": "计算机科学", "description": "硅谷创业教父Paul Graham的文集，探讨了计算机编程的本质和黑客文化。", "location": "3F-A区-04架"},
    {"title": "点石成金：访客至上的网页设计秘笈", "author": "Steve Krug", "isbn": "9787111402183", "category": "设计", "description": "网页可用性设计的经典之作，以幽默风趣的方式阐述了用户至上的设计理念。", "location": "4F-A区-02架"},
]


def seed_books(db):
    """种子图书数据"""
    print("=" * 60)
    print("导入图书数据...")
    print("=" * 60)

    from app.models.book import Book

    count = 0
    for bk in FALLBACK_BOOKS:
        existing = db.query(Book).filter(Book.title == bk["title"]).first()
        if not existing:
            book = Book(
                title=bk["title"],
                author=bk["author"],
                isbn=bk["isbn"],
                category=bk["category"],
                description=bk["description"],
                location=bk["location"],
                status="available",
            )
            db.add(book)
            count += 1

    db.commit()
    print(f"  >> 成功导入 {count} 本图书\n")
    return count


# =============================================================================
# 第三阶段：抓取政策文档
# =============================================================================
POLICY_URLS = [
    {
        "url": "https://lib.shu.edu.cn/gybengua/gui_zhang_zh/jygd.htm",
        "category": "借阅规定",
        "title": "上海大学图书馆借阅规定",
    },
    {
        "url": "https://lib.shu.edu.cn/gybengua/gui_zhang_zh/dzxz/tsgrgxz.htm",
        "category": "入馆须知",
        "title": "上海大学图书馆入馆须知",
    },
    {
        "url": "https://lib.shu.edu.cn/gybengua/kai_fang_s/qwztsg.htm",
        "category": "开放时间",
        "title": "上海大学图书馆开放时间",
    },
]


def scrape_policies(db):
    """爬取上海大学图书馆政策文档"""
    print("=" * 60)
    print("抓取上海大学图书馆政策文档...")
    print("=" * 60)

    from app.models.policy_doc import PolicyDoc

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    count = 0
    for item in POLICY_URLS:
        url = item["url"]
        try:
            resp = session.get(url, timeout=15)
            resp.encoding = "utf-8"
            if resp.status_code != 200:
                print(f"  !! {item['title']} HTTP {resp.status_code}")
                continue

            html = resp.text
            soup = BeautifulSoup(html, "lxml")

            for tag in soup(["script", "style"]):
                tag.decompose()

            content_div = (
                soup.select_one("#content")
                or soup.select_one(".content")
                or soup.select_one("#main")
                or soup.select_one("article")
                or soup.select_one("body")
            )

            text = content_div.get_text(separator="\n", strip=True) if content_div else soup.get_text(separator="\n", strip=True)

            lines = []
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if "当前位置" in line or "您现在所在" in line:
                    continue
                if "版权所有" in line or ("上海大学" in line and "图书馆" not in line and "开放" not in line):
                    continue
                lines.append(line)

            clean_text = "\n\n".join(lines)

            existing = db.query(PolicyDoc).filter(PolicyDoc.title == item["title"]).first()
            if existing:
                existing.content = clean_text
            else:
                doc = PolicyDoc(
                    title=item["title"],
                    content=clean_text,
                    category=item["category"],
                    source_url=url,
                )
                db.add(doc)
            count += 1
            print(f"  + {item['title']}: {len(clean_text)} 字符")

        except requests.exceptions.RequestException as e:
            print(f"  !! {item['title']} 请求失败: {e}")

    db.commit()
    print(f"  >> 成功处理 {count} 篇政策文档\n")
    return count


# =============================================================================
# 第四阶段：生成座位数据
# =============================================================================
SEAT_LAYOUT = [
    ("3F", "静音区", "standard", 12),
    ("3F", "讨论区", "standard", 10),
    ("3F", "电子阅览区", "computer", 8),
    ("4F", "静音区", "standard", 14),
    ("4F", "单人区", "double", 8),
    ("4F", "休闲区", "standard", 8),
    ("5F", "静音区", "standard", 10),
    ("5F", "讨论区", "standard", 10),
    ("5F", "单人区", "double", 10),
]

ZONE_PREFIX = {"静音区": "A", "讨论区": "B", "单人区": "D", "休闲区": "C", "电子阅览区": "C"}


def generate_seats(db):
    """生成座位数据"""
    print("=" * 60)
    print("生成座位数据...")
    print("=" * 60)

    from app.models.seat import Seat

    count = 0
    for floor, zone, seat_type, num in SEAT_LAYOUT:
        prefix = ZONE_PREFIX.get(zone, "A")
        for i in range(1, num + 1):
            code = f"{floor}-{prefix}{i:02d}"
            existing = db.query(Seat).filter(Seat.code == code).first()
            if not existing:
                seat = Seat(
                    code=code, floor=floor, zone=zone,
                    seat_type=seat_type, status="available", version=1,
                )
                db.add(seat)
                count += 1

    db.commit()
    print(f"  >> 成功生成 {count} 个座位\n")
    return count


# =============================================================================
# 第五阶段：构建 ChromaDB 向量索引
# =============================================================================
import asyncio


async def build_indexes(db):
    """构建 ChromaDB 向量索引"""
    print("=" * 60)
    print("构建 ChromaDB 向量索引...")
    print("=" * 60)

    from app.models.book import Book
    from app.models.policy_doc import PolicyDoc
    from app.retrieval.chunker import TextChunker
    from app.retrieval.embedding import EmbeddingService
    from app.core.chromadb_client import ChromaClient

    chunker = TextChunker()
    embedder = EmbeddingService()
    chroma = ChromaClient()

    # 图书索引
    print("  处理图书索引...")
    books_coll = chroma.get_or_create_collection("library_books")
    books = db.query(Book).all()
    book_chunks = []
    for book in books:
        book_chunks.extend(chunker.chunk_book({
            "id": str(book.id), "title": book.title,
            "author": book.author or "", "description": book.description or "",
        }))
    if book_chunks:
        texts = [c["text"] for c in book_chunks]
        metadatas = [{k: str(v) for k, v in c.items() if k != "text"} for c in book_chunks]
        ids = [f"book_{i}" for i in range(len(book_chunks))]
        embeddings = await embedder.embed_documents(texts)
        books_coll.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
        print(f"  + 图书索引: {len(book_chunks)} 个分块")
    else:
        print("  !! 没有图书数据，跳过")

    # 政策索引
    print("  处理政策索引...")
    policies_coll = chroma.get_or_create_collection("library_policies")
    docs = db.query(PolicyDoc).all()
    policy_chunks = []
    for doc in docs:
        policy_chunks.extend(chunker.chunk_policy({
            "id": str(doc.id), "title": doc.title,
            "content": doc.content, "category": doc.category or "",
        }))
    if policy_chunks:
        texts = [c["text"] for c in policy_chunks]
        metadatas = [{k: str(v) for k, v in c.items() if k != "text"} for c in policy_chunks]
        ids = [f"policy_{i}" for i in range(len(policy_chunks))]
        embeddings = await embedder.embed_documents(texts)
        policies_coll.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
        print(f"  + 政策索引: {len(policy_chunks)} 个分块")
    else:
        print("  !! 没有政策数据，跳过")
    print()


# =============================================================================
# 验证
# =============================================================================
def verify(db):
    """验证数据完整性"""
    print("=" * 60)
    print("验证数据完整性...")
    print("=" * 60)

    from app.models.book import Book
    from app.models.policy_doc import PolicyDoc
    from app.models.seat import Seat
    from app.core.chromadb_client import ChromaClient

    bc = db.query(Book).count()
    pc = db.query(PolicyDoc).count()
    sc = db.query(Seat).count()
    print(f"  图书: {bc} 本")
    print(f"  政策: {pc} 篇")
    print(f"  座位: {sc} 个")

    chroma = ChromaClient()
    for name in ["library_books", "library_policies"]:
        try:
            c = chroma.get_or_create_collection(name)
            print(f"  ChromaDB '{name}': {c.count()} 个向量")
        except Exception as e:
            print(f"  ChromaDB '{name}': {e}")

    return bc >= 10


# =============================================================================
# 主入口
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="图书馆数据种子脚本")
    parser.add_argument("--clear-only", action="store_true", help="仅清空数据")
    parser.add_argument("--skip-scrape", action="store_true", help="跳过抓取")
    parser.add_argument("--skip-index", action="store_true", help="跳过索引构建")
    args = parser.parse_args()

    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    from app.core.database import SessionLocal, init_db
    from app.config import settings

    print("图书馆数据种子脚本")
    print(f"  数据库: {settings.DATABASE_URL}")
    print()

    init_db()
    db = SessionLocal()
    try:
        if args.clear_only:
            clear_data(db)
            return

        if not args.skip_scrape:
            clear_data(db)
            bc = seed_books(db)
            pc = scrape_policies(db)
            sc = generate_seats(db)
            print(f"插入汇总: {bc} 本图书, {pc} 篇政策, {sc} 个座位\n")

        if not args.skip_index:
            asyncio.run(build_indexes(db))

        ok = verify(db)
        print(f"\n{'完成!' if ok else '部分验证未通过'}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
