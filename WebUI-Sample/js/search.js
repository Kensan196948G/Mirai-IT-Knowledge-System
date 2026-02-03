/**
 * Search Engine
 * 全文検索、フィルタリング、ソート機能を提供
 */

class SearchEngine {
  constructor() {
    this.storageManager = new StorageManager();
  }

  /**
   * ナレッジアイテムを検索
   * @param {Object} options - 検索オプション
   * @param {string} options.query - 検索クエリ
   * @param {Array} options.itsmTypes - ITSMタイプフィルタ
   * @param {Array} options.tags - タグフィルタ
   * @param {string} options.severity - 重要度フィルタ
   * @param {string} options.status - ステータスフィルタ
   * @param {string} options.sortBy - ソート項目（created_at, updated_at, title）
   * @param {string} options.sortOrder - ソート順序（asc, desc）
   * @param {number} options.limit - 結果の最大件数
   * @param {number} options.offset - 結果のオフセット
   * @returns {Object} 検索結果
   */
  search(options = {}) {
    try {
      const {
        query = '',
        itsmTypes = [],
        tags = [],
        severity = null,
        status = null,
        sortBy = 'updated_at',
        sortOrder = 'desc',
        limit = null,
        offset = 0
      } = options;

      let items = this.storageManager.getAllKnowledge();

      // クエリによる全文検索
      if (query && query.trim()) {
        items = this._fullTextSearch(items, query);
      }

      // ITSMタイプでフィルタ
      if (itsmTypes && itsmTypes.length > 0) {
        items = items.filter(item =>
          itsmTypes.includes(item.itsm_type)
        );
      }

      // タグでフィルタ
      if (tags && tags.length > 0) {
        items = items.filter(item =>
          item.tags && item.tags.some(tag => tags.includes(tag))
        );
      }

      // 重要度でフィルタ
      if (severity) {
        items = items.filter(item => item.severity === severity);
      }

      // ステータスでフィルタ
      if (status) {
        items = items.filter(item => item.status === status);
      }

      // ソート
      items = this._sortItems(items, sortBy, sortOrder);

      // 総数を保存
      const totalCount = items.length;

      // ページネーション
      if (limit !== null) {
        items = items.slice(offset, offset + limit);
      }

      return {
        items: items,
        total: totalCount,
        limit: limit,
        offset: offset,
        hasMore: limit !== null && (offset + limit) < totalCount
      };
    } catch (error) {
      console.error('Search failed:', error);
      return {
        items: [],
        total: 0,
        limit: limit,
        offset: offset,
        hasMore: false,
        error: error.message
      };
    }
  }

  /**
   * 全文検索を実行
   * @param {Array} items - アイテムリスト
   * @param {string} query - 検索クエリ
   * @returns {Array} マッチしたアイテム
   */
  _fullTextSearch(items, query) {
    const queryLower = query.toLowerCase();
    const terms = queryLower.split(/\s+/).filter(t => t.length > 0);

    return items.filter(item => {
      const searchText = this._getSearchableText(item).toLowerCase();

      // 全てのタームが含まれているかチェック
      return terms.every(term => searchText.includes(term));
    }).map(item => {
      // 検索スコアを計算
      const score = this._calculateSearchScore(item, query);
      return { ...item, _searchScore: score };
    }).sort((a, b) => b._searchScore - a._searchScore);
  }

  /**
   * アイテムから検索可能なテキストを取得
   * @param {Object} item - アイテム
   * @returns {string} 検索可能テキスト
   */
  _getSearchableText(item) {
    const parts = [
      item.title || '',
      item.content || '',
      item.itsm_type || '',
      (item.tags || []).join(' '),
      item.severity || '',
      item.status || ''
    ];
    return parts.join(' ');
  }

  /**
   * 検索スコアを計算
   * @param {Object} item - アイテム
   * @param {string} query - 検索クエリ
   * @returns {number} スコア
   */
  _calculateSearchScore(item, query) {
    const queryLower = query.toLowerCase();
    let score = 0;

    // タイトルマッチは高スコア
    if (item.title && item.title.toLowerCase().includes(queryLower)) {
      score += 10;
    }

    // コンテンツマッチは中スコア
    if (item.content && item.content.toLowerCase().includes(queryLower)) {
      score += 5;
    }

    // タグマッチは中スコア
    if (item.tags && item.tags.some(tag => tag.toLowerCase().includes(queryLower))) {
      score += 5;
    }

    // ITSMタイプマッチは低スコア
    if (item.itsm_type && item.itsm_type.toLowerCase().includes(queryLower)) {
      score += 3;
    }

    // 複数回出現する場合はスコアを増やす
    const searchText = this._getSearchableText(item).toLowerCase();
    const matches = (searchText.match(new RegExp(queryLower, 'g')) || []).length;
    score += matches;

    return score;
  }

  /**
   * アイテムをソート
   * @param {Array} items - アイテムリスト
   * @param {string} sortBy - ソート項目
   * @param {string} sortOrder - ソート順序
   * @returns {Array} ソートされたアイテム
   */
  _sortItems(items, sortBy, sortOrder) {
    const sorted = [...items].sort((a, b) => {
      let aVal, bVal;

      switch (sortBy) {
        case 'created_at':
        case 'updated_at':
          aVal = new Date(a[sortBy] || 0);
          bVal = new Date(b[sortBy] || 0);
          break;
        case 'title':
          aVal = (a.title || '').toLowerCase();
          bVal = (b.title || '').toLowerCase();
          break;
        case 'itsm_type':
          aVal = (a.itsm_type || '').toLowerCase();
          bVal = (b.itsm_type || '').toLowerCase();
          break;
        case 'severity':
          aVal = this._severityToNumber(a.severity);
          bVal = this._severityToNumber(b.severity);
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }

  /**
   * 重要度を数値に変換
   * @param {string} severity - 重要度
   * @returns {number} 数値
   */
  _severityToNumber(severity) {
    const map = {
      critical: 4,
      high: 3,
      medium: 2,
      low: 1
    };
    return map[severity] || 0;
  }

  /**
   * ファセット情報を取得（フィルタリング用の統計情報）
   * @param {Array} items - アイテムリスト（省略時は全アイテム）
   * @returns {Object} ファセット情報
   */
  getFacets(items = null) {
    try {
      if (!items) {
        items = this.storageManager.getAllKnowledge();
      }

      const facets = {
        itsmTypes: this._countByField(items, 'itsm_type'),
        tags: this._countAllTags(items),
        severities: this._countByField(items, 'severity'),
        statuses: this._countByField(items, 'status')
      };

      return facets;
    } catch (error) {
      console.error('Failed to get facets:', error);
      return {
        itsmTypes: {},
        tags: {},
        severities: {},
        statuses: {}
      };
    }
  }

  /**
   * フィールドごとにカウント
   * @param {Array} items - アイテムリスト
   * @param {string} field - フィールド名
   * @returns {Object} カウント結果
   */
  _countByField(items, field) {
    const counts = {};
    items.forEach(item => {
      const value = item[field];
      if (value) {
        counts[value] = (counts[value] || 0) + 1;
      }
    });
    return counts;
  }

  /**
   * 全タグをカウント
   * @param {Array} items - アイテムリスト
   * @returns {Object} カウント結果
   */
  _countAllTags(items) {
    const counts = {};
    items.forEach(item => {
      if (item.tags && Array.isArray(item.tags)) {
        item.tags.forEach(tag => {
          counts[tag] = (counts[tag] || 0) + 1;
        });
      }
    });
    return counts;
  }

  /**
   * サジェストを取得（オートコンプリート用）
   * @param {string} query - 入力クエリ
   * @param {number} limit - 最大件数
   * @returns {Array} サジェストリスト
   */
  getSuggestions(query, limit = 5) {
    try {
      if (!query || query.trim().length < 2) {
        return [];
      }

      const queryLower = query.toLowerCase();
      const items = this.storageManager.getAllKnowledge();
      const suggestions = new Set();

      // タイトルから抽出
      items.forEach(item => {
        if (item.title && item.title.toLowerCase().includes(queryLower)) {
          suggestions.add(item.title);
        }
      });

      // タグから抽出
      items.forEach(item => {
        if (item.tags && Array.isArray(item.tags)) {
          item.tags.forEach(tag => {
            if (tag.toLowerCase().includes(queryLower)) {
              suggestions.add(tag);
            }
          });
        }
      });

      return Array.from(suggestions).slice(0, limit);
    } catch (error) {
      console.error('Failed to get suggestions:', error);
      return [];
    }
  }

  /**
   * 類似アイテムを検索
   * @param {string} itemId - アイテムID
   * @param {number} limit - 最大件数
   * @returns {Array} 類似アイテム
   */
  findSimilar(itemId, limit = 5) {
    try {
      const targetItem = this.storageManager.getKnowledgeById(itemId);
      if (!targetItem) {
        return [];
      }

      const items = this.storageManager.getAllKnowledge()
        .filter(item => item.id !== itemId);

      // 類似度を計算
      const scored = items.map(item => ({
        ...item,
        _similarity: this._calculateSimilarity(targetItem, item)
      }));

      // 類似度でソートして上位を返す
      return scored
        .sort((a, b) => b._similarity - a._similarity)
        .slice(0, limit);
    } catch (error) {
      console.error('Failed to find similar items:', error);
      return [];
    }
  }

  /**
   * 類似度を計算
   * @param {Object} item1 - アイテム1
   * @param {Object} item2 - アイテム2
   * @returns {number} 類似度スコア
   */
  _calculateSimilarity(item1, item2) {
    let score = 0;

    // ITSMタイプが同じ
    if (item1.itsm_type === item2.itsm_type) {
      score += 10;
    }

    // タグの重複
    if (item1.tags && item2.tags) {
      const commonTags = item1.tags.filter(tag => item2.tags.includes(tag));
      score += commonTags.length * 5;
    }

    // 重要度が同じ
    if (item1.severity === item2.severity) {
      score += 3;
    }

    // タイトルの単語の重複
    if (item1.title && item2.title) {
      const words1 = new Set(item1.title.toLowerCase().split(/\s+/));
      const words2 = new Set(item2.title.toLowerCase().split(/\s+/));
      const commonWords = [...words1].filter(w => words2.has(w));
      score += commonWords.length * 2;
    }

    return score;
  }

  /**
   * 高度な検索（複雑なクエリ）
   * @param {string} queryString - クエリ文字列（例: "tag:apache AND type:Incident"）
   * @returns {Object} 検索結果
   */
  advancedSearch(queryString) {
    try {
      // クエリをパース
      const parsedQuery = this._parseAdvancedQuery(queryString);

      // 検索オプションに変換
      const options = {
        query: parsedQuery.text || '',
        itsmTypes: parsedQuery.types || [],
        tags: parsedQuery.tags || [],
        severity: parsedQuery.severity || null,
        status: parsedQuery.status || null
      };

      return this.search(options);
    } catch (error) {
      console.error('Advanced search failed:', error);
      return {
        items: [],
        total: 0,
        error: error.message
      };
    }
  }

  /**
   * 高度なクエリをパース
   * @param {string} queryString - クエリ文字列
   * @returns {Object} パース結果
   */
  _parseAdvancedQuery(queryString) {
    const result = {
      text: '',
      types: [],
      tags: [],
      severity: null,
      status: null
    };

    // タグ検索: tag:apache
    const tagMatches = queryString.match(/tag:(\w+)/g);
    if (tagMatches) {
      result.tags = tagMatches.map(m => m.replace('tag:', ''));
      queryString = queryString.replace(/tag:\w+/g, '');
    }

    // タイプ検索: type:Incident
    const typeMatches = queryString.match(/type:(\w+)/g);
    if (typeMatches) {
      result.types = typeMatches.map(m => m.replace('type:', ''));
      queryString = queryString.replace(/type:\w+/g, '');
    }

    // 重要度検索: severity:high
    const severityMatch = queryString.match(/severity:(\w+)/);
    if (severityMatch) {
      result.severity = severityMatch[1];
      queryString = queryString.replace(/severity:\w+/g, '');
    }

    // ステータス検索: status:resolved
    const statusMatch = queryString.match(/status:(\w+)/);
    if (statusMatch) {
      result.status = statusMatch[1];
      queryString = queryString.replace(/status:\w+/g, '');
    }

    // 残りはテキスト検索
    result.text = queryString.replace(/AND|OR/g, '').trim();

    return result;
  }
}

// グローバルインスタンスをエクスポート
const searchEngine = new SearchEngine();
