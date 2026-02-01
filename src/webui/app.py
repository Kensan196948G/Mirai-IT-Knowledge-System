"""
WebUI Application
Flask-based Web Interface for Knowledge Management

環境対応版 - Phase 4実装
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
from pathlib import Path
import sys
import os
import logging
from datetime import datetime
import json
import html as html_lib
import re
import urllib.parse
import urllib.request
from typing import Dict, Any

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 環境設定読み込み
from src.config.environment import load_environment, get_config

# 環境を決定（環境変数またはデフォルト）
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
env_config = load_environment(ENVIRONMENT)

from src.core.workflow import WorkflowEngine
from src.core.itsm_classifier import ITSMClassifier
from src.mcp.sqlite_client import SQLiteClient
from src.mcp.feedback_client import FeedbackClient
from src.workflows.interactive_knowledge_creation import (
    InteractiveKnowledgeCreationWorkflow,
)
from src.workflows.intelligent_search import IntelligentSearchAssistant
from src.workflows.workflow_studio_engine import WorkflowStudioEngine

# ログ設定
log_level = getattr(logging, env_config.get('log_level', 'DEBUG').upper(), logging.DEBUG)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            env_config.get('log_path', project_root / 'data' / 'logs') / env_config.get('log_file', 'app.log'),
            encoding='utf-8'
        ) if Path(env_config.get('log_path', project_root / 'data' / 'logs')).exists() else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Server Fault / DeepL helpers
_TRANSLATION_CACHE = {}


def _strip_html(raw_html: str) -> str:
    if not raw_html:
        return ''
    text = re.sub(r'<[^>]+>', ' ', raw_html)
    text = html_lib.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _truncate(text: str, limit: int = 240) -> str:
    if not text:
        return ''
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + '...'


def _translate_texts(texts, api_key, target_lang, api_url):
    if not api_key:
        return texts, False

    results = list(texts)
    index_map = []
    payload_texts = []
    for idx, text in enumerate(texts):
        if not text:
            continue
        cached = _TRANSLATION_CACHE.get(text)
        if cached is not None:
            results[idx] = cached
            continue
        index_map.append(idx)
        payload_texts.append(text)

    if not payload_texts:
        return results, True

    translated_success = True
    batch_size = 50
    for start in range(0, len(payload_texts), batch_size):
        batch = payload_texts[start:start + batch_size]
        batch_indices = index_map[start:start + batch_size]
        try:
            data = [('auth_key', api_key), ('target_lang', target_lang)]
            for text in batch:
                data.append(('text', text))
            body = urllib.parse.urlencode(data, doseq=True).encode('utf-8')
            req = urllib.request.Request(api_url, data=body, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            with urllib.request.urlopen(req, timeout=15) as resp:
                payload = json.loads(resp.read().decode('utf-8'))
            translations = payload.get('translations', [])
            if len(translations) != len(batch):
                raise ValueError('DeepL response count mismatch')
            for i, item in enumerate(translations):
                translated_text = item.get('text', batch[i])
                results[batch_indices[i]] = translated_text
                _TRANSLATION_CACHE[batch[i]] = translated_text
        except Exception as exc:
            logger.warning(f"DeepL翻訳エラー: {exc}")
            translated_success = False
            for i, original in enumerate(batch):
                results[batch_indices[i]] = original

    return results, translated_success


def _fetch_serverfault_questions(page, pagesize, sort, order, tagged, api_base):
    params = {
        'site': 'serverfault',
        'page': page,
        'pagesize': pagesize,
        'order': order,
        'sort': sort,
        'filter': 'withbody'
    }
    if tagged:
        params['tagged'] = tagged
    query = urllib.parse.urlencode(params, doseq=True)
    url = f"{api_base}/questions?{query}"

    with urllib.request.urlopen(url, timeout=15) as resp:
        payload = json.loads(resp.read().decode('utf-8'))

    items = []
    for item in payload.get('items', []):
        body_text = _strip_html(item.get('body', ''))
        items.append({
            'question_id': item.get('question_id'),
            'title': item.get('title', ''),
            'excerpt': _truncate(body_text, 240),
            'tags': item.get('tags', []),
            'score': item.get('score', 0),
            'answer_count': item.get('answer_count', 0),
            'view_count': item.get('view_count', 0),
            'is_answered': item.get('is_answered', False),
            'has_accepted_answer': bool(item.get('accepted_answer_id')),
            'link': item.get('link', ''),
            'creation_date': item.get('creation_date')
        })

    return items, payload


def _fetch_serverfault_answers(question_id, sort, order, api_base):
    params = {
        'site': 'serverfault',
        'order': order,
        'sort': sort,
        'filter': 'withbody'
    }
    query = urllib.parse.urlencode(params, doseq=True)
    url = f"{api_base}/questions/{question_id}/answers?{query}"

    with urllib.request.urlopen(url, timeout=15) as resp:
        payload = json.loads(resp.read().decode('utf-8'))

    items = []
    for item in payload.get('items', []):
        body_text = _strip_html(item.get('body', ''))
        items.append({
            'answer_id': item.get('answer_id'),
            'question_id': question_id,
            'score': item.get('score', 0),
            'is_accepted': item.get('is_accepted', False),
            'excerpt': _truncate(body_text, 280),
            'body': body_text
        })

    return items, payload

# 環境別Flask設定
app.config["SECRET_KEY"] = env_config.get('secret_key', 'mirai-it-knowledge-systems-secret-key')
app.config["DEBUG"] = env_config.get('flask_debug', True)
app.config["ENV"] = env_config.get('flask_env', 'development')

# セッションCookie設定
app.config["SESSION_COOKIE_SECURE"] = env_config.get('session_cookie_secure', True)
app.config["SESSION_COOKIE_HTTPONLY"] = env_config.get('session_cookie_httponly', True)
app.config["SESSION_COOKIE_SAMESITE"] = env_config.get('session_cookie_samesite', 'Lax')

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# 環境情報をテンプレートに自動注入
@app.context_processor
def inject_environment():
    """テンプレートに環境情報を注入"""
    return {
        'environment': ENVIRONMENT,
        'is_development': ENVIRONMENT == 'development',
        'is_production': ENVIRONMENT == 'production',
        'app_version': '3.0.0',
        'use_sample_data': env_config.get('use_sample_data', True),
        'base_url': env_config.get('base_url', f"https://{env_config.get('host', 'localhost')}:{env_config.get('port', 8888)}")
    }

logger.info(f"🚀 アプリケーション起動: 環境={ENVIRONMENT}, ポート={env_config.get('port', 8888)}")

# グローバルインスタンス

db_client = SQLiteClient(str(env_config.get('database_path', 'db/knowledge.db')))
feedback_client = FeedbackClient(str(env_config.get('database_path', 'db/knowledge.db')))
workflow_engine = WorkflowEngine()
itsm_classifier = ITSMClassifier()
intelligent_search = IntelligentSearchAssistant()
workflow_studio_engine = WorkflowStudioEngine()

# セッション管理（簡易版）
chat_sessions = {}


def _get_chat_workflow(
    session_id: str, user_id: str
) -> InteractiveKnowledgeCreationWorkflow:
    if session_id not in chat_sessions:
        chat_sessions[session_id] = InteractiveKnowledgeCreationWorkflow()
        db_client.create_conversation_session(session_id, user_id)
    return chat_sessions[session_id]


def _process_chat_message(
    session_id: str, message: str, user_id: str
) -> Dict[str, Any]:
    workflow = _get_chat_workflow(session_id, user_id)

    db_client.add_conversation_message(session_id, "user", message)

    if len(workflow.conversation_history) == 0:
        result = workflow.start_conversation(message)
    else:
        result = workflow.answer_question(message)

    assistant_message = None
    if result.get("type") == "question":
        assistant_message = result.get("question")
    elif result.get("type") == "knowledge_generated":
        assistant_message = f"ナレッジ案を生成しました: {result.get('title', '')}"

    if assistant_message:
        db_client.add_conversation_message(session_id, "assistant", assistant_message)

    return result


@app.route("/")
def index():
    """トップページ"""
    # 統計情報を取得
    stats = db_client.get_statistics()

    # 最近のナレッジを取得
    recent_knowledge = db_client.search_knowledge(limit=5)

    return render_template("index.html", stats=stats, recent_knowledge=recent_knowledge)


@app.route("/knowledge/search", methods=["GET", "POST"])
def search_knowledge():
    """ナレッジ検索"""
    # GETパラメータからも検索条件を受け取る（統計カードクリック時）
    if request.method == "GET" and request.args.get("itsm_type"):
        itsm_type = request.args.get("itsm_type")
        results = db_client.search_knowledge(itsm_type=itsm_type, limit=50)
        return render_template(
            "search_results.html", query="", results=results, itsm_type_filter=itsm_type
        )

    if request.method == "POST":
        query = request.form.get("query", "")
        itsm_type = request.form.get("itsm_type", "")
        tags = (
            request.form.get("tags", "").split(",")
            if request.form.get("tags")
            else None
        )

        results = db_client.search_knowledge(
            query=query if query else None,
            itsm_type=itsm_type if itsm_type else None,
            tags=tags,
            limit=50,
        )

        return render_template(
            "search_results.html",
            query=query,
            results=results,
            itsm_type_filter=itsm_type,
        )

    # パラメータなしの場合: ナレッジ一覧とFAQ一覧を表示
    # ナレッジ一覧（Incident, Problem, Change, Release）
    knowledge_list = db_client.search_knowledge(limit=50)
    knowledge_list = [k for k in knowledge_list if k.get("itsm_type") != "Request"]

    # FAQ一覧（Request = FAQ）
    faq_list = db_client.search_knowledge(itsm_type="Request", limit=50)

    return render_template(
        "knowledge_list.html",
        knowledge_list=knowledge_list,
        faq_list=faq_list
    )


@app.route("/knowledge/<int:knowledge_id>")
def view_knowledge(knowledge_id):
    """ナレッジ詳細表示"""
    knowledge = db_client.get_knowledge(knowledge_id)
    if not knowledge:
        return "ナレッジが見つかりません", 404

    # 関連ナレッジを取得
    related = db_client.get_related_knowledge(knowledge_id)

    # 使用統計を記録
    try:
        feedback_client.log_knowledge_usage(knowledge_id, "view", user_id="webui_user")
    except:
        pass  # エラーがあっても表示は継続

    # パンくずリスト用
    breadcrumb_items = [
        {"name": "ナレッジ", "url": "/knowledge/search"},
        {"name": knowledge["title"][:50], "url": None},
    ]

    return render_template(
        "knowledge_detail.html",
        knowledge=knowledge,
        related=related,
        breadcrumb_items=breadcrumb_items,
    )


@app.route("/knowledge/create", methods=["GET", "POST"])
def create_knowledge():
    """新規ナレッジ作成"""
    if request.method == "POST":
        title = request.form.get("title", "")
        content = request.form.get("content", "")
        itsm_type = request.form.get("itsm_type", "")
        created_by = request.form.get("created_by", "webui_user")

        # ITSMタイプが指定されていない場合は自動分類
        if not itsm_type or itsm_type == "auto":
            classification = itsm_classifier.classify(title, content)
            itsm_type = classification["itsm_type"]

        # ワークフロー実行
        result = workflow_engine.process_knowledge(
            title=title, content=content, itsm_type=itsm_type, created_by=created_by
        )

        if result["success"]:
            # 成功メッセージ付きでリダイレクト
            return redirect(
                url_for(
                    "view_knowledge",
                    knowledge_id=result["knowledge_id"],
                    success=1,
                    message="ナレッジを作成しました",
                )
            )
        else:
            return render_template("create.html", error=result.get("error"))

    return render_template("create.html")


# ===== ヘルスチェックAPI =====
@app.route("/api/health", methods=["GET"])
def api_health():
    """
    ヘルスチェックAPI

    自動エラー検知・修復システム用のエンドポイント
    """
    import shutil
    import sqlite3

    health_status = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "checks": {},
        "environment": ENVIRONMENT
    }

    # 1. データベース接続チェック
    try:
        db_path = env_config.get('database_path', project_root / 'db' / 'knowledge.db')
        conn = sqlite3.connect(str(db_path), timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
        count = cursor.fetchone()[0]
        conn.close()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": f"Connected, {count} entries"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        health_status["status"] = "degraded"

    # 2. ディスク容量チェック
    try:
        disk = shutil.disk_usage("/")
        usage_percent = (disk.used / disk.total) * 100
        free_gb = disk.free / (1024 ** 3)
        health_status["checks"]["disk"] = {
            "status": "healthy" if usage_percent < 90 else "unhealthy",
            "usage_percent": round(usage_percent, 1),
            "free_gb": round(free_gb, 1)
        }
        if usage_percent >= 90:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["disk"] = {
            "status": "unhealthy",
            "message": str(e)
        }

    # 3. ログディレクトリチェック
    log_path = env_config.get('log_path', project_root / 'logs')
    health_status["checks"]["logs"] = {
        "status": "healthy" if Path(log_path).exists() else "unhealthy",
        "path": str(log_path)
    }

    # 4. 全体ステータス判定
    for check in health_status["checks"].values():
        if check.get("status") == "unhealthy":
            health_status["status"] = "critical"
            break

    status_code = 200 if health_status["status"] == "healthy" else (
        503 if health_status["status"] == "critical" else 200
    )

    return jsonify(health_status), status_code


@app.route("/api/classify", methods=["POST"])
def api_classify():
    """ITSM分類API"""
    data = request.get_json()
    title = data.get("title", "")
    content = data.get("content", "")

    classification = itsm_classifier.classify(title, content)
    candidates = itsm_classifier.suggest_itsm_type(title, content, threshold=0.3)

    return jsonify({"classification": classification, "candidates": candidates})


@app.route("/api/knowledge", methods=["GET"])
def api_get_knowledge():
    """ナレッジ取得API"""
    knowledge_id = request.args.get("id", type=int)
    if knowledge_id:
        knowledge = db_client.get_knowledge(knowledge_id)
        return jsonify(knowledge) if knowledge else ("", 404)

    # 検索
    query = request.args.get("query")
    itsm_type = request.args.get("itsm_type")
    limit = request.args.get("limit", 20, type=int)

    results = db_client.search_knowledge(query=query, itsm_type=itsm_type, limit=limit)

    return jsonify(results)


@app.route("/api/statistics", methods=["GET"])
def api_statistics():
    """統計情報API"""
    stats = db_client.get_statistics()
    return jsonify(stats)


@app.route("/dashboard")
def dashboard():
    """ダッシュボード"""
    stats = db_client.get_statistics()

    # ワークフロー実行履歴（最新10件）
    with db_client.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM workflow_executions
            ORDER BY created_at DESC
            LIMIT 10
        """)
        workflow_history = [dict(row) for row in cursor.fetchall()]

    return render_template(
        "dashboard.html", stats=stats, workflow_history=workflow_history
    )


# ========== フィードバック機能 ==========


@app.route("/knowledge/<int:knowledge_id>/feedback", methods=["POST"])
def add_knowledge_feedback(knowledge_id):
    """ナレッジへのフィードバック追加"""
    rating = request.form.get("rating", type=int)
    feedback_type = request.form.get("feedback_type")
    comment = request.form.get("comment")
    user_id = request.form.get("user_id", "anonymous")

    feedback_client.add_knowledge_feedback(
        knowledge_id=knowledge_id,
        user_id=user_id,
        rating=rating,
        feedback_type=feedback_type,
        comment=comment,
    )

    # 使用統計も記録
    feedback_client.log_knowledge_usage(knowledge_id, "feedback", user_id)

    return redirect(url_for("view_knowledge", knowledge_id=knowledge_id))


@app.route("/feedback", methods=["GET", "POST"])
def system_feedback():
    """システムフィードバック"""
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category")
        priority = request.form.get("priority", "medium")
        user_id = request.form.get("user_id", "anonymous")

        feedback_client.add_system_feedback(
            title=title,
            description=description,
            feedback_category=category,
            user_id=user_id,
            priority=priority,
        )

        return redirect(url_for("system_feedback"))

    # フィードバック一覧を取得
    feedbacks = feedback_client.get_system_feedback(limit=50)
    return render_template("system_feedback.html", feedbacks=feedbacks)


@app.route("/analytics")
def analytics():
    """分析ダッシュボード"""
    # フィードバックサマリー
    feedback_summary = feedback_client.get_feedback_summary()

    # 人気のナレッジ
    popular_knowledge = feedback_client.get_popular_knowledge(limit=10, days=30)

    # 評価の高いナレッジ
    top_rated = feedback_client.get_top_rated_knowledge(limit=10)

    return render_template(
        "analytics.html",
        feedback_summary=feedback_summary,
        popular_knowledge=popular_knowledge,
        top_rated=top_rated,
    )


@app.route("/api/knowledge/<int:knowledge_id>/stats", methods=["GET"])
def api_knowledge_stats(knowledge_id):
    """ナレッジ統計API"""
    usage_stats = feedback_client.get_knowledge_usage_stats(knowledge_id)
    rating = feedback_client.get_knowledge_rating(knowledge_id)

    return jsonify({"usage_stats": usage_stats, "rating": rating})


@app.route("/api/knowledge/<int:knowledge_id>", methods=["DELETE"])
def api_delete_knowledge(knowledge_id):
    """ナレッジ削除API"""
    try:
        # ナレッジの存在確認
        knowledge = sqlite_client.get_knowledge_by_id(knowledge_id)
        if not knowledge:
            return jsonify({"error": "ナレッジが見つかりません"}), 404

        # 削除実行（論理削除: statusを'deleted'に更新）
        sqlite_client.execute_query(
            "UPDATE knowledge SET status = 'deleted', updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), knowledge_id)
        )

        logger.info(f"ナレッジ削除: ID={knowledge_id}, タイトル={knowledge.get('title', 'Unknown')}")

        return jsonify({
            "success": True,
            "message": "ナレッジを削除しました",
            "id": knowledge_id
        })

    except Exception as e:
        logger.error(f"ナレッジ削除エラー: {e}")
        return jsonify({"error": str(e)}), 500


# ========== AI対話機能 ==========


@app.route("/chat")
def chat():
    """AI対話ナレッジ作成ページ"""
    return render_template("chat.html", now=datetime.now().strftime("%H:%M"))


@app.route("/api/chat/message", methods=["POST"])
def chat_message():
    """チャットメッセージ処理"""
    data = request.get_json()
    session_id = data.get("session_id")
    message = data.get("message")
    user_id = data.get("user_id", "webui_user")

    if not session_id or not message:
        return jsonify({"error": "session_idとmessageが必要です"}), 400

    result = _process_chat_message(session_id, message, user_id)

    return jsonify(result)


@app.route("/api/chat/save", methods=["POST"])
def chat_save():
    """対話で生成したナレッジを保存"""
    data = request.get_json()
    title = data.get("title")
    content = data.get("content")
    itsm_type = data.get("itsm_type")
    session_id = data.get("session_id")
    conversation_history = data.get("conversation_history", [])

    # ワークフロー実行
    result = workflow_engine.process_knowledge(
        title=title, content=content, itsm_type=itsm_type, created_by="ai_chat"
    )

    if session_id:
        db_client.complete_conversation_session(
            session_id, result.get("knowledge_id") if result.get("success") else None
        )

    # セッションをクリーンアップ
    if session_id in chat_sessions:
        del chat_sessions[session_id]

    return jsonify(result)


def _run_async_orchestrator(orchestrator, question, context=None):
    """非同期オーケストレーターを同期的に実行するヘルパー"""
    import asyncio
    import concurrent.futures

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Flaskなど既存ループ内で実行中の場合
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    orchestrator.process(question, context)
                )
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(
                orchestrator.process(question, context)
            )
    except RuntimeError:
        # ループがない場合は新規作成
        return asyncio.run(orchestrator.process(question, context))


@app.route("/api/chat/ai-answer", methods=["POST"])
def chat_ai_answer():
    """AI駆動の回答を生成（AIオーケストレーター使用）"""
    data = request.get_json()
    question = data.get("question", "")
    session_id = data.get("session_id")

    if not question:
        return jsonify({"success": False, "error": "質問が必要です"})

    try:
        # セッションからワークフローを取得
        workflow = None
        if session_id and session_id in chat_sessions:
            workflow = chat_sessions[session_id].get("workflow")

        if workflow:
            # ワークフローのAI回答機能を使用
            result = workflow.get_ai_answer(question)
        else:
            # 直接AIオーケストレーターを使用
            from src.ai.orchestrator import get_orchestrator

            orchestrator = get_orchestrator()
            ai_result = _run_async_orchestrator(orchestrator, question)

            result = {
                'success': True,
                'answer': ai_result.answer,
                'evidence': ai_result.evidence,
                'sources': ai_result.sources,
                'confidence': ai_result.confidence,
                'ai_used': ai_result.ai_used,
                'processing_time_ms': ai_result.processing_time_ms
            }

        return jsonify(result)

    except Exception as e:
        logger.error(f"AI回答生成エラー: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "answer": "回答を生成できませんでした。しばらくしてからお試しください。"
        })


@app.route("/api/chat/feedback", methods=["POST"])
def chat_feedback():
    """チャット回答への評価を保存"""
    data = request.get_json() or {}
    session_id = data.get("session_id")
    message_id = data.get("message_id")
    rating = data.get("rating")
    user_id = data.get("user_id", "webui_user")

    if not session_id or not message_id or rating not in (-1, 1):
        return jsonify({"success": False, "error": "invalid payload"}), 400

    try:
        feedback_client.add_chat_feedback(
            session_id=session_id,
            message_id=message_id,
            rating=rating,
            user_id=user_id
        )
        return jsonify({"success": True})
    except Exception as exc:
        logger.error(f"chat_feedback error: {exc}")
        return jsonify({"success": False, "error": "failed to save feedback"}), 500


@socketio.on("ai_question")
def handle_ai_question(data):
    """WebSocket経由のAI質問処理"""
    session_id = data.get("session_id")
    question = data.get("question", "")

    if not question:
        emit("ai_error", {"error": "質問が必要です"})
        return

    try:
        # AIオーケストレーターで回答生成
        from src.ai.orchestrator import get_orchestrator

        orchestrator = get_orchestrator()
        result = _run_async_orchestrator(orchestrator, question)

        emit("ai_answer", {
            'success': True,
            'answer': result.answer,
            'evidence': result.evidence,
            'sources': result.sources,
            'confidence': result.confidence,
            'ai_used': result.ai_used,
            'processing_time_ms': result.processing_time_ms
        }, to=session_id if session_id else request.sid)

    except Exception as e:
        logger.error(f"AI質問処理エラー: {e}")
        emit("ai_error", {
            "success": False,
            "error": str(e),
            "message": "AI回答の生成中にエラーが発生しました。"
        })


@socketio.on("join_chat")
def handle_join_chat(data):
    """チャットセッション参加"""
    session_id = data.get("session_id")
    if not session_id:
        emit("chat_error", {"error": "session_idが必要です"})
        return

    join_room(session_id)
    emit("chat_joined", {"session_id": session_id})


@socketio.on("chat_message")
def handle_socket_chat_message(data):
    """WebSocket経由のチャット処理"""
    session_id = data.get("session_id")
    message = data.get("message")
    user_id = data.get("user_id", "webui_user")

    if not session_id or not message:
        emit("chat_error", {"error": "session_idとmessageが必要です"})
        return

    result = _process_chat_message(session_id, message, user_id)

    if result.get("type") == "question":
        emit("chat_response", result, to=session_id)
    elif result.get("type") == "knowledge_generated":
        emit("chat_generated", result, to=session_id)
    else:
        emit("chat_response", result, to=session_id)


# ========== インテリジェント検索 ==========


@app.route("/search/intelligent")
def intelligent_search_page():
    """インテリジェント検索ページ"""
    return render_template("intelligent_search.html")


@app.route("/api/search/intelligent", methods=["POST"])
def api_intelligent_search():
    """インテリジェント検索API"""
    data = request.get_json()
    query = data.get("query", "")

    if not query:
        return jsonify({"error": "クエリが空です"}), 400

    # インテリジェント検索実行
    result = intelligent_search.search(query)

    try:
        db_client.log_search_history(
            search_query=query,
            search_type="natural_language",
            filters={"intent": result.get("intent")},
            results_count=len(result.get("knowledge", [])),
            user_id=request.remote_addr,
        )
    except Exception:
        pass

    return jsonify(result)


# ========== ワークフロー監視 ==========


@app.route("/workflows/monitor")
def workflow_monitor():
    """ワークフロー実行モニタリング"""
    executions = db_client.get_recent_workflow_executions(limit=20)
    return render_template("workflow_monitor.html", executions=executions)


@app.route("/api/workflows/recent", methods=["GET"])
def api_recent_workflows():
    """最近のワークフロー実行を取得"""
    limit = request.args.get("limit", 20, type=int)
    return jsonify(db_client.get_recent_workflow_executions(limit=limit))


@app.route("/api/workflows/<int:execution_id>", methods=["GET"])
def api_workflow_detail(execution_id):
    """ワークフロー実行詳細を取得"""
    execution = db_client.get_workflow_execution(execution_id)
    if not execution:
        return jsonify({"error": "not found"}), 404

    return jsonify(
        {
            "execution": execution,
            "subagent_logs": db_client.get_subagent_logs(execution_id),
            "hook_logs": db_client.get_hook_logs(execution_id),
        }
    )


@app.route("/api/workflows/run", methods=["POST"])
def api_run_workflow():
    """Workflow Studioのワークフローを実行"""
    data = request.get_json() or {}
    workflow_name = data.get("workflow")
    inputs = data.get("inputs", {})

    if not workflow_name:
        return jsonify({"error": "workflowが必要です"}), 400

    result = workflow_studio_engine.run_workflow(
        workflow_name, inputs, user_id=request.remote_addr
    )
    return jsonify(result)


# ========== Server Fault ==========


@app.route("/serverfault")
def serverfault_browser():
    """Server Fault質問ブラウジングページ"""
    return render_template("serverfault.html")


@app.route("/api/serverfault/questions", methods=["GET"])
def api_serverfault_questions():
    """Server Fault質問取得API（日本語翻訳付き）"""
    page = request.args.get("page", default=1, type=int)
    pagesize = request.args.get("pagesize", default=20, type=int)
    sort = request.args.get("sort", default="activity")
    order = request.args.get("order", default="desc")
    tagged = request.args.get("tag")
    translate = request.args.get("translate", default="true").lower() in ("true", "1", "yes", "on")

    api_base = env_config.get('serverfault_api_base', 'https://api.stackexchange.com/2.3')
    api_base = api_base.rstrip('/')

    try:
        items, payload = _fetch_serverfault_questions(page, pagesize, sort, order, tagged, api_base)
    except Exception as exc:
        logger.error(f"Server Fault取得エラー: {exc}")
        return jsonify({"success": False, "error": "質問の取得に失敗しました"}), 502

    translated = False
    if translate:
        api_key = env_config.get('deepl_api_key', '')
        target_lang = env_config.get('deepl_target_lang', 'JA')
        api_url = env_config.get('deepl_api_url', 'https://api.deepl.com/v2/translate')

        jobs = []
        for idx, item in enumerate(items):
            item['title_original'] = item.get('title', '')
            item['excerpt_original'] = item.get('excerpt', '')
            item['tags_original'] = item.get('tags', [])
            jobs.append(('title', idx, None, item['title_original']))
            jobs.append(('excerpt', idx, None, item['excerpt_original']))
            for tag_index, tag in enumerate(item['tags_original']):
                jobs.append(('tag', idx, tag_index, tag))

        texts = [job[3] for job in jobs]
        translated_texts, translated = _translate_texts(texts, api_key, target_lang, api_url)

        for job, translated_text in zip(jobs, translated_texts):
            kind, item_index, tag_index, _ = job
            if kind == 'title':
                items[item_index]['title'] = translated_text
            elif kind == 'excerpt':
                items[item_index]['excerpt'] = translated_text
            elif kind == 'tag':
                tags = items[item_index].get('tags', [])
                while len(tags) <= tag_index:
                    tags.append('')
                tags[tag_index] = translated_text
                items[item_index]['tags'] = tags

        for item in items:
            if 'tags' not in item:
                item['tags'] = item.get('tags_original', [])

    response = jsonify({
        "success": True,
        "items": items,
        "has_more": payload.get("has_more", False),
        "quota_remaining": payload.get("quota_remaining"),
        "translated": translated
    })
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/api/serverfault/answers", methods=["GET"])
def api_serverfault_answers():
    """Server Fault回答取得API（日本語翻訳付き）"""
    question_id = request.args.get("question_id", type=int)
    if not question_id:
        return jsonify({"success": False, "error": "question_idが必要です"}), 400

    sort = request.args.get("sort", default="votes")
    order = request.args.get("order", default="desc")
    translate = request.args.get("translate", default="true").lower() in ("true", "1", "yes", "on")

    api_base = env_config.get('serverfault_api_base', 'https://api.stackexchange.com/2.3')
    api_base = api_base.rstrip('/')

    try:
        items, payload = _fetch_serverfault_answers(question_id, sort, order, api_base)
    except Exception as exc:
        logger.error(f"Server Fault回答取得エラー: {exc}")
        return jsonify({"success": False, "error": "回答の取得に失敗しました"}), 502

    translated = False
    if translate:
        api_key = env_config.get('deepl_api_key', '')
        target_lang = env_config.get('deepl_target_lang', 'JA')
        api_url = env_config.get('deepl_api_url', 'https://api.deepl.com/v2/translate')

        jobs = []
        for idx, item in enumerate(items):
            item['body_original'] = item.get('body', '')
            item['excerpt_original'] = item.get('excerpt', '')
            jobs.append(('body', idx, item['body_original']))
            jobs.append(('excerpt', idx, item['excerpt_original']))

        texts = [job[2] for job in jobs]
        translated_texts, translated = _translate_texts(texts, api_key, target_lang, api_url)

        for job, translated_text in zip(jobs, translated_texts):
            kind, item_index, _ = job
            if kind == 'body':
                items[item_index]['body'] = translated_text
            elif kind == 'excerpt':
                items[item_index]['excerpt'] = translated_text

    response = jsonify({
        "success": True,
        "items": items,
        "has_more": payload.get("has_more", False),
        "quota_remaining": payload.get("quota_remaining"),
        "translated": translated
    })
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# ========== Codex Skills ==========


@app.route("/api/codex/skill", methods=["POST"])
def api_codex_skill():
    """Codex Skills API"""
    data = request.get_json() or {}

    try:
        from src.core.codex_skills import SkillRouter

        router = SkillRouter()
        result = router.execute(data)
        return jsonify({"success": True, "result": result})
    except PermissionError as e:
        return jsonify({"success": False, "error": str(e)}), 403
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Codex skill execution error: {e}")
        return jsonify({"success": False, "error": "skill execution failed"}), 500


# ========== 設定機能 ==========


@app.route("/settings")
def settings():
    """設定ページ"""
    return render_template("settings.html")


@app.route("/api/settings/authenticate", methods=["POST"])
def api_settings_authenticate():
    """設定変更用の認証"""
    data = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")

    # 簡易認証（本番環境ではハッシュ化したパスワードと照合）
    # デフォルト: admin / admin123
    if username == "admin" and password == "admin123":
        # トークン生成（簡易版）
        import secrets

        token = secrets.token_urlsafe(32)

        return jsonify({"success": True, "token": token, "username": username})
    else:
        return jsonify(
            {"success": False, "error": "ユーザー名またはパスワードが正しくありません"}
        ), 401


@app.route("/api/settings/save", methods=["POST"])
def api_settings_save():
    """設定を保存"""
    # 認証トークン確認（簡易版）
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return jsonify({"success": False, "error": "認証が必要です"}), 401

    data = request.get_json()
    settings = data.get("settings", {})

    # 設定をファイルに保存（簡易実装）
    # 本番環境ではデータベースに保存
    try:
        import json
        from pathlib import Path

        config_file = Path("config/runtime_settings.json")
        config_file.parent.mkdir(exist_ok=True)

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

        return jsonify({"success": True, "message": "設定を保存しました"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    import socket

    # 環境設定から取得
    HOST = env_config.get('host', '0.0.0.0')
    PORT = env_config.get('port', 8888)
    DEBUG = env_config.get('flask_debug', True)
    SSL_ENABLED = env_config.get('ssl_enabled', False)
    SSL_CERT = env_config.get('ssl_cert', '')
    SSL_KEY = env_config.get('ssl_key', '')

    # 環境バッジ
    env_badge = "🔧 開発" if ENVIRONMENT == 'development' else "🚀 本番"
    protocol = "https" if SSL_ENABLED else "http"

    print("")
    print("=" * 60)
    print(f"🌐 Mirai IT Knowledge Systems - WebUI [{env_badge}]")
    print("=" * 60)
    print(f"   環境: {ENVIRONMENT}")
    print(f"   ポート: {PORT}")
    print(f"   デバッグ: {DEBUG}")
    print(f"   SSL/HTTPS: {SSL_ENABLED}")
    print("")
    print(f"   アクセスURL:")
    print(f"   {protocol}://{HOST}:{PORT}")
    print(f"   {protocol}://localhost:{PORT}")
    print("")

    if ENVIRONMENT == 'development':
        print("   📝 開発環境: サンプルデータが有効です")
    else:
        print("   ⚠️  本番環境: サンプルデータは無効です")

    print("")
    print("   終了するには Ctrl+C を押してください")
    print("=" * 60)
    print("")

    # SSL設定
    ssl_context = None
    if SSL_ENABLED and Path(SSL_CERT).exists() and Path(SSL_KEY).exists():
        ssl_context = (SSL_CERT, SSL_KEY)
        logger.info(f"SSL有効: {SSL_CERT}")
    elif SSL_ENABLED:
        logger.warning("SSL証明書が見つかりません。HTTPで起動します。")
        logger.warning(f"  証明書パス: {SSL_CERT}")
        logger.warning(f"  キーパス: {SSL_KEY}")

    # Flask-SocketIO起動
    socketio.run(
        app,
        host='0.0.0.0',
        port=PORT,
        debug=DEBUG,
        ssl_context=ssl_context,
        allow_unsafe_werkzeug=True
    )
