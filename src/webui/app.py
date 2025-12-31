"""
WebUI Application
Flask-based Web Interface for Knowledge Management
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pathlib import Path
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.workflow import WorkflowEngine
from src.core.itsm_classifier import ITSMClassifier
from src.mcp.sqlite_client import SQLiteClient
from src.mcp.feedback_client import FeedbackClient
from src.workflows.interactive_knowledge_creation import InteractiveKnowledgeCreationWorkflow
from src.workflows.intelligent_search import IntelligentSearchAssistant

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mirai-it-knowledge-systems-secret-key'

# グローバルインスタンス
db_client = SQLiteClient()
feedback_client = FeedbackClient()
workflow_engine = WorkflowEngine()
itsm_classifier = ITSMClassifier()
intelligent_search = IntelligentSearchAssistant()

# セッション管理（簡易版）
chat_sessions = {}


@app.route('/')
def index():
    """トップページ"""
    # 統計情報を取得
    stats = db_client.get_statistics()

    # 最近のナレッジを取得
    recent_knowledge = db_client.search_knowledge(limit=5)

    return render_template('index.html', stats=stats, recent_knowledge=recent_knowledge)


@app.route('/knowledge/search', methods=['GET', 'POST'])
def search_knowledge():
    """ナレッジ検索"""
    # GETパラメータからも検索条件を受け取る（統計カードクリック時）
    if request.method == 'GET' and request.args.get('itsm_type'):
        itsm_type = request.args.get('itsm_type')
        results = db_client.search_knowledge(
            itsm_type=itsm_type,
            limit=50
        )
        return render_template('search_results.html', query='', results=results, itsm_type_filter=itsm_type)

    if request.method == 'POST':
        query = request.form.get('query', '')
        itsm_type = request.form.get('itsm_type', '')
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else None

        results = db_client.search_knowledge(
            query=query if query else None,
            itsm_type=itsm_type if itsm_type else None,
            tags=tags,
            limit=50
        )

        return render_template('search_results.html', query=query, results=results, itsm_type_filter=itsm_type)

    return render_template('search.html')


@app.route('/knowledge/<int:knowledge_id>')
def view_knowledge(knowledge_id):
    """ナレッジ詳細表示"""
    knowledge = db_client.get_knowledge(knowledge_id)
    if not knowledge:
        return "ナレッジが見つかりません", 404

    # 関連ナレッジを取得
    related = db_client.get_related_knowledge(knowledge_id)

    # 使用統計を記録
    try:
        feedback_client.log_knowledge_usage(knowledge_id, 'view', user_id='webui_user')
    except:
        pass  # エラーがあっても表示は継続

    # パンくずリスト用
    breadcrumb_items = [
        {'name': 'ナレッジ', 'url': '/knowledge/search'},
        {'name': knowledge['title'][:50], 'url': None}
    ]

    return render_template('knowledge_detail.html', knowledge=knowledge, related=related, breadcrumb_items=breadcrumb_items)


@app.route('/knowledge/create', methods=['GET', 'POST'])
def create_knowledge():
    """新規ナレッジ作成"""
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        itsm_type = request.form.get('itsm_type', '')
        created_by = request.form.get('created_by', 'webui_user')

        # ITSMタイプが指定されていない場合は自動分類
        if not itsm_type or itsm_type == 'auto':
            classification = itsm_classifier.classify(title, content)
            itsm_type = classification['itsm_type']

        # ワークフロー実行
        result = workflow_engine.process_knowledge(
            title=title,
            content=content,
            itsm_type=itsm_type,
            created_by=created_by
        )

        if result['success']:
            # 成功メッセージ付きでリダイレクト
            return redirect(url_for('view_knowledge', knowledge_id=result['knowledge_id'], success=1, message='ナレッジを作成しました'))
        else:
            return render_template('create.html', error=result.get('error'))

    return render_template('create.html')


@app.route('/api/classify', methods=['POST'])
def api_classify():
    """ITSM分類API"""
    data = request.get_json()
    title = data.get('title', '')
    content = data.get('content', '')

    classification = itsm_classifier.classify(title, content)
    candidates = itsm_classifier.suggest_itsm_type(title, content, threshold=0.3)

    return jsonify({
        'classification': classification,
        'candidates': candidates
    })


@app.route('/api/knowledge', methods=['GET'])
def api_get_knowledge():
    """ナレッジ取得API"""
    knowledge_id = request.args.get('id', type=int)
    if knowledge_id:
        knowledge = db_client.get_knowledge(knowledge_id)
        return jsonify(knowledge) if knowledge else ('', 404)

    # 検索
    query = request.args.get('query')
    itsm_type = request.args.get('itsm_type')
    limit = request.args.get('limit', 20, type=int)

    results = db_client.search_knowledge(
        query=query,
        itsm_type=itsm_type,
        limit=limit
    )

    return jsonify(results)


@app.route('/api/statistics', methods=['GET'])
def api_statistics():
    """統計情報API"""
    stats = db_client.get_statistics()
    return jsonify(stats)


@app.route('/dashboard')
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

    return render_template('dashboard.html', stats=stats, workflow_history=workflow_history)


# ========== フィードバック機能 ==========

@app.route('/knowledge/<int:knowledge_id>/feedback', methods=['POST'])
def add_knowledge_feedback(knowledge_id):
    """ナレッジへのフィードバック追加"""
    rating = request.form.get('rating', type=int)
    feedback_type = request.form.get('feedback_type')
    comment = request.form.get('comment')
    user_id = request.form.get('user_id', 'anonymous')

    feedback_client.add_knowledge_feedback(
        knowledge_id=knowledge_id,
        user_id=user_id,
        rating=rating,
        feedback_type=feedback_type,
        comment=comment
    )

    # 使用統計も記録
    feedback_client.log_knowledge_usage(knowledge_id, 'feedback', user_id)

    return redirect(url_for('view_knowledge', knowledge_id=knowledge_id))


@app.route('/feedback', methods=['GET', 'POST'])
def system_feedback():
    """システムフィードバック"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        priority = request.form.get('priority', 'medium')
        user_id = request.form.get('user_id', 'anonymous')

        feedback_client.add_system_feedback(
            title=title,
            description=description,
            feedback_category=category,
            user_id=user_id,
            priority=priority
        )

        return redirect(url_for('system_feedback'))

    # フィードバック一覧を取得
    feedbacks = feedback_client.get_system_feedback(limit=50)
    return render_template('system_feedback.html', feedbacks=feedbacks)


@app.route('/analytics')
def analytics():
    """分析ダッシュボード"""
    # フィードバックサマリー
    feedback_summary = feedback_client.get_feedback_summary()

    # 人気のナレッジ
    popular_knowledge = feedback_client.get_popular_knowledge(limit=10, days=30)

    # 評価の高いナレッジ
    top_rated = feedback_client.get_top_rated_knowledge(limit=10)

    return render_template(
        'analytics.html',
        feedback_summary=feedback_summary,
        popular_knowledge=popular_knowledge,
        top_rated=top_rated
    )


@app.route('/api/knowledge/<int:knowledge_id>/stats', methods=['GET'])
def api_knowledge_stats(knowledge_id):
    """ナレッジ統計API"""
    usage_stats = feedback_client.get_knowledge_usage_stats(knowledge_id)
    rating = feedback_client.get_knowledge_rating(knowledge_id)

    return jsonify({
        'usage_stats': usage_stats,
        'rating': rating
    })


# ========== AI対話機能 ==========

@app.route('/chat')
def chat():
    """AI対話ナレッジ作成ページ"""
    return render_template('chat.html', now=datetime.now().strftime('%H:%M'))


@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """チャットメッセージ処理"""
    data = request.get_json()
    session_id = data.get('session_id')
    message = data.get('message')
    collected_data = data.get('collected_data', {})

    # セッション取得または作成
    if session_id not in chat_sessions:
        chat_sessions[session_id] = InteractiveKnowledgeCreationWorkflow()

    workflow = chat_sessions[session_id]

    # 最初のメッセージか？
    if len(workflow.conversation_history) == 0:
        result = workflow.start_conversation(message)
    else:
        result = workflow.answer_question(message)

    return jsonify(result)


@app.route('/api/chat/save', methods=['POST'])
def chat_save():
    """対話で生成したナレッジを保存"""
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    itsm_type = data.get('itsm_type')
    session_id = data.get('session_id')
    conversation_history = data.get('conversation_history', [])

    # ワークフロー実行
    result = workflow_engine.process_knowledge(
        title=title,
        content=content,
        itsm_type=itsm_type,
        created_by='ai_chat'
    )

    # セッションをクリーンアップ
    if session_id in chat_sessions:
        del chat_sessions[session_id]

    return jsonify(result)


# ========== インテリジェント検索 ==========

@app.route('/search/intelligent')
def intelligent_search_page():
    """インテリジェント検索ページ"""
    return render_template('intelligent_search.html')


@app.route('/api/search/intelligent', methods=['POST'])
def api_intelligent_search():
    """インテリジェント検索API"""
    data = request.get_json()
    query = data.get('query', '')

    if not query:
        return jsonify({'error': 'クエリが空です'}), 400

    # インテリジェント検索実行
    result = intelligent_search.search(query)

    return jsonify(result)


if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    PORT = 8888

    print("🌐 Mirai IT Knowledge Systems - WebUI")
    print(f"   http://{ip_address}:{PORT}")
    print(f"   http://localhost:{PORT}")
    print("")
    print("終了するには Ctrl+C を押してください")
    print("")
    app.run(host='0.0.0.0', port=PORT, debug=True)
