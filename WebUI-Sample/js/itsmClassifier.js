/**
 * ITSM Classifier
 * ITSM自動分類ロジック（Python実装のJavaScript移植版）
 * 参考: Z:\Mirai-IT-Knowledge-Systems\src\core\itsm_classifier.py
 */

class ITSMClassifier {
  constructor() {
    this.classificationRules = this._loadClassificationRules();
  }

  /**
   * タイトルと内容からITSMタイプを分類
   * @param {string} title - タイトル
   * @param {string} content - 内容
   * @returns {Object} 分類結果
   */
  classify(title, content) {
    const text = (title + ' ' + content).toLowerCase();

    const scores = {};
    for (const [itsmType, rules] of Object.entries(this.classificationRules)) {
      scores[itsmType] = this._calculateScore(text, rules);
    }

    // 最高スコアのITSMタイプを選択
    if (Object.keys(scores).length === 0) {
      return {
        itsm_type: 'Other',
        confidence: 0.0,
        scores: {},
        reason: '分類ルールが適用されませんでした'
      };
    }

    const sortedScores = Object.entries(scores).sort((a, b) => b[1] - a[1]);
    const [itsmType, confidence] = sortedScores[0];

    // 信頼度が低い場合はOther
    let finalType = itsmType;
    let reason;

    if (confidence < 0.3) {
      finalType = 'Other';
      reason = '明確なITSMタイプが判定できませんでした';
    } else {
      reason = `${itsmType}の特徴的なキーワードが検出されました`;
    }

    return {
      itsm_type: finalType,
      confidence: Math.round(confidence * 100) / 100,
      scores: Object.fromEntries(
        Object.entries(scores).map(([k, v]) => [k, Math.round(v * 100) / 100])
      ),
      reason: reason
    };
  }

  /**
   * 複数のITSMタイプ候補を提案
   * @param {string} title - タイトル
   * @param {string} content - 内容
   * @param {number} threshold - スコア閾値（これ以上のスコアのみ返す）
   * @returns {Array} 候補リスト
   */
  suggestItsmType(title, content, threshold = 0.5) {
    const result = this.classify(title, content);
    const scores = result.scores;

    // 閾値以上のものを抽出
    const candidates = Object.entries(scores)
      .filter(([_, score]) => score >= threshold)
      .map(([itsmType, score]) => ({
        itsm_type: itsmType,
        score: Math.round(score * 100) / 100,
        is_primary: itsmType === result.itsm_type
      }))
      .sort((a, b) => b.score - a.score);

    return candidates;
  }

  /**
   * テキストに対するキーワードマッチング詳細を取得
   * @param {string} title - タイトル
   * @param {string} content - 内容
   * @returns {Object} マッチング詳細
   */
  getMatchingDetails(title, content) {
    const text = (title + ' ' + content).toLowerCase();
    const details = {};

    for (const [itsmType, rules] of Object.entries(this.classificationRules)) {
      const primaryMatches = this._getMatchedKeywords(text, rules.primary_keywords);
      const secondaryMatches = this._getMatchedKeywords(text, rules.secondary_keywords);

      details[itsmType] = {
        primary_matches: primaryMatches,
        secondary_matches: secondaryMatches,
        primary_count: primaryMatches.length,
        secondary_count: secondaryMatches.length,
        score: this._calculateScore(text, rules)
      };
    }

    return details;
  }

  /**
   * 分類ルールを定義
   * @returns {Object} 分類ルール
   */
  _loadClassificationRules() {
    return {
      Incident: {
        primary_keywords: [
          '障害', 'インシデント', 'incident', 'エラー', 'error',
          '異常', '停止', 'ダウン', 'down', '緊急', 'アラート',
          'alert', '発生', 'failure', '失敗', 'crash'
        ],
        secondary_keywords: [
          '復旧', '対応', '影響', '検知', '通知', 'recovery',
          'restore', '再起動', 'restart', '回復', 'fix'
        ],
        weight_primary: 0.6,
        weight_secondary: 0.4
      },
      Problem: {
        primary_keywords: [
          '問題', 'problem', '根本原因', 'root cause', 'root-cause',
          '再発', '傾向', '分析', '真因', '恒久対策', 'analysis',
          'permanent', 'recurring', '繰り返し'
        ],
        secondary_keywords: [
          '調査', '特定', '対策', '改善', '防止', 'investigation',
          'identify', 'prevention', 'improvement', 'measure'
        ],
        weight_primary: 0.7,
        weight_secondary: 0.3
      },
      Change: {
        primary_keywords: [
          '変更', 'change', '改修', '適用', 'パッチ', 'patch',
          '更新', 'update', '修正', 'modification', 'alter',
          '設定変更', 'configuration'
        ],
        secondary_keywords: [
          '計画', 'スケジュール', '承認', 'ロールバック', 'rollback',
          'テスト', 'test', 'リスク', 'risk', '影響評価',
          'approval', 'schedule', 'plan'
        ],
        weight_primary: 0.6,
        weight_secondary: 0.4
      },
      Release: {
        primary_keywords: [
          'リリース', 'release', 'デプロイ', 'deploy', '展開',
          '本番', 'production', 'リリースノート', 'deployment',
          'rollout', 'go-live', 'launch'
        ],
        secondary_keywords: [
          '機能', 'feature', 'バージョン', 'version', 'ビルド',
          'build', 'ロールアウト', '段階的', 'phased', '新機能'
        ],
        weight_primary: 0.7,
        weight_secondary: 0.3
      },
      Request: {
        primary_keywords: [
          '依頼', '要求', 'request', 'リクエスト', '申請',
          'サービスリクエスト', 'サービス要求', 'service request',
          '申し込み', 'application'
        ],
        secondary_keywords: [
          '承認', 'approval', '許可', '権限', 'アクセス', 'access',
          '追加', '削除', 'permission', 'grant', 'revoke',
          'add', 'remove'
        ],
        weight_primary: 0.6,
        weight_secondary: 0.4
      }
    };
  }

  /**
   * テキストに対するスコアを計算
   * @param {string} text - 分析対象テキスト
   * @param {Object} rules - 分類ルール
   * @returns {number} スコア（0.0〜1.0）
   */
  _calculateScore(text, rules) {
    const primaryKeywords = rules.primary_keywords || [];
    const secondaryKeywords = rules.secondary_keywords || [];
    const weightPrimary = rules.weight_primary || 0.5;
    const weightSecondary = rules.weight_secondary || 0.5;

    // プライマリキーワードのマッチ数
    const primaryMatches = primaryKeywords.filter(keyword =>
      text.includes(keyword.toLowerCase())
    ).length;
    const primaryScore = Math.min(1.0, primaryMatches / Math.max(1, primaryKeywords.length));

    // セカンダリキーワードのマッチ数
    const secondaryMatches = secondaryKeywords.filter(keyword =>
      text.includes(keyword.toLowerCase())
    ).length;
    const secondaryScore = Math.min(1.0, secondaryMatches / Math.max(1, secondaryKeywords.length));

    // 重み付けスコア
    const totalScore = (primaryScore * weightPrimary) + (secondaryScore * weightSecondary);

    return totalScore;
  }

  /**
   * マッチしたキーワードのリストを取得
   * @param {string} text - 分析対象テキスト
   * @param {Array} keywords - キーワードリスト
   * @returns {Array} マッチしたキーワード
   */
  _getMatchedKeywords(text, keywords) {
    return keywords.filter(keyword =>
      text.includes(keyword.toLowerCase())
    );
  }

  /**
   * 全ITSMタイプの説明を取得
   * @returns {Object} ITSMタイプの説明
   */
  getItsmTypeDescriptions() {
    return {
      Incident: {
        name: 'インシデント',
        description: 'サービスの中断や品質低下を引き起こす予期しない事象',
        icon: '🔴',
        priority: 'high',
        examples: [
          'サーバーダウン',
          'アプリケーションエラー',
          'ネットワーク障害'
        ]
      },
      Problem: {
        name: '問題管理',
        description: '1つ以上のインシデントの根本原因',
        icon: '🔍',
        priority: 'medium',
        examples: [
          '根本原因分析',
          '再発防止策の策定',
          'システムの脆弱性の特定'
        ]
      },
      Change: {
        name: '変更管理',
        description: 'ITインフラやサービスの計画的な変更',
        icon: '🔧',
        priority: 'medium',
        examples: [
          '設定変更',
          'パッチ適用',
          'システム改修'
        ]
      },
      Release: {
        name: 'リリース管理',
        description: '新機能やバージョンの本番環境への展開',
        icon: '🚀',
        priority: 'high',
        examples: [
          'アプリケーションのデプロイ',
          '新機能のリリース',
          'バージョンアップグレード'
        ]
      },
      Request: {
        name: 'サービスリクエスト',
        description: 'ユーザーからのサービス提供依頼',
        icon: '📝',
        priority: 'low',
        examples: [
          'アクセス権限申請',
          'アカウント作成依頼',
          'リソース追加要求'
        ]
      },
      Other: {
        name: 'その他',
        description: '上記のカテゴリに分類されない事項',
        icon: '❓',
        priority: 'low',
        examples: [
          '一般的な質問',
          'ドキュメント',
          '未分類の項目'
        ]
      }
    };
  }

  /**
   * 分類信頼度のレベルを取得
   * @param {number} confidence - 信頼度（0.0〜1.0）
   * @returns {Object} 信頼度レベル情報
   */
  getConfidenceLevel(confidence) {
    if (confidence >= 0.7) {
      return {
        level: 'high',
        label: '高',
        color: 'green',
        description: '非常に高い確信度で分類されました'
      };
    } else if (confidence >= 0.5) {
      return {
        level: 'medium',
        label: '中',
        color: 'yellow',
        description: '中程度の確信度で分類されました'
      };
    } else if (confidence >= 0.3) {
      return {
        level: 'low',
        label: '低',
        color: 'orange',
        description: '低い確信度で分類されました。手動確認を推奨します'
      };
    } else {
      return {
        level: 'very-low',
        label: '極低',
        color: 'red',
        description: '分類の確信度が非常に低いため、手動での分類が必要です'
      };
    }
  }
}

// グローバルインスタンスをエクスポート
const itsmClassifier = new ITSMClassifier();
