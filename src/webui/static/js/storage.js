/**
 * LocalStorage Management Class
 * LocalStorageを使用したナレッジデータのCRUD操作とインポート/エクスポート機能を提供
 */

class StorageManager {
  constructor() {
    this.STORAGE_KEY_KNOWLEDGE = 'mirai_knowledge_items';
    this.STORAGE_KEY_QUESTIONS = 'mirai_server_fault_questions';
    this.STORAGE_KEY_SETTINGS = 'mirai_settings';
  }

  /**
   * ナレッジアイテムを全て取得
   * @returns {Array} ナレッジアイテムの配列
   */
  getAllKnowledge() {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY_KNOWLEDGE);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Failed to load knowledge items:', error);
      return [];
    }
  }

  /**
   * IDでナレッジアイテムを取得
   * @param {string} id - ナレッジID
   * @returns {Object|null} ナレッジアイテム
   */
  getKnowledgeById(id) {
    try {
      const items = this.getAllKnowledge();
      return items.find(item => item.id === id) || null;
    } catch (error) {
      console.error('Failed to get knowledge item:', error);
      return null;
    }
  }

  /**
   * ナレッジアイテムを保存
   * @param {Object} item - ナレッジアイテム
   * @returns {boolean} 成功したかどうか
   */
  saveKnowledge(item) {
    try {
      const items = this.getAllKnowledge();

      // 新規作成時はIDと作成日時を付与
      if (!item.id) {
        item.id = this._generateId();
        item.created_at = new Date().toISOString();
      }

      // 更新日時を設定
      item.updated_at = new Date().toISOString();

      // 既存アイテムを更新または新規追加
      const index = items.findIndex(i => i.id === item.id);
      if (index >= 0) {
        items[index] = item;
      } else {
        items.push(item);
      }

      localStorage.setItem(this.STORAGE_KEY_KNOWLEDGE, JSON.stringify(items));
      return true;
    } catch (error) {
      console.error('Failed to save knowledge item:', error);
      return false;
    }
  }

  /**
   * ナレッジアイテムを削除
   * @param {string} id - ナレッジID
   * @returns {boolean} 成功したかどうか
   */
  deleteKnowledge(id) {
    try {
      const items = this.getAllKnowledge();
      const filtered = items.filter(item => item.id !== id);

      if (filtered.length === items.length) {
        return false; // アイテムが見つからなかった
      }

      localStorage.setItem(this.STORAGE_KEY_KNOWLEDGE, JSON.stringify(filtered));
      return true;
    } catch (error) {
      console.error('Failed to delete knowledge item:', error);
      return false;
    }
  }

  /**
   * 複数のナレッジアイテムを一括保存
   * @param {Array} items - ナレッジアイテムの配列
   * @returns {boolean} 成功したかどうか
   */
  saveAllKnowledge(items) {
    try {
      localStorage.setItem(this.STORAGE_KEY_KNOWLEDGE, JSON.stringify(items));
      return true;
    } catch (error) {
      console.error('Failed to save all knowledge items:', error);
      return false;
    }
  }

  /**
   * Server Fault質問を全て取得
   * @returns {Array} 質問の配列
   */
  getAllQuestions() {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY_QUESTIONS);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Failed to load questions:', error);
      return [];
    }
  }

  /**
   * Server Fault質問を保存
   * @param {Array} questions - 質問の配列
   * @returns {boolean} 成功したかどうか
   */
  saveAllQuestions(questions) {
    try {
      localStorage.setItem(this.STORAGE_KEY_QUESTIONS, JSON.stringify(questions));
      return true;
    } catch (error) {
      console.error('Failed to save questions:', error);
      return false;
    }
  }

  /**
   * 設定を取得
   * @returns {Object} 設定オブジェクト
   */
  getSettings() {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY_SETTINGS);
      return data ? JSON.parse(data) : this._getDefaultSettings();
    } catch (error) {
      console.error('Failed to load settings:', error);
      return this._getDefaultSettings();
    }
  }

  /**
   * 設定を保存
   * @param {Object} settings - 設定オブジェクト
   * @returns {boolean} 成功したかどうか
   */
  saveSettings(settings) {
    try {
      localStorage.setItem(this.STORAGE_KEY_SETTINGS, JSON.stringify(settings));
      return true;
    } catch (error) {
      console.error('Failed to save settings:', error);
      return false;
    }
  }

  /**
   * データをJSONファイルとしてエクスポート
   * @param {string} type - 'knowledge' または 'questions'
   */
  exportData(type = 'knowledge') {
    try {
      let data, filename;

      if (type === 'knowledge') {
        data = this.getAllKnowledge();
        filename = `mirai-knowledge-${this._getDateString()}.json`;
      } else if (type === 'questions') {
        data = this.getAllQuestions();
        filename = `mirai-questions-${this._getDateString()}.json`;
      } else {
        throw new Error('Invalid export type');
      }

      const json = JSON.stringify(data, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      return true;
    } catch (error) {
      console.error('Failed to export data:', error);
      return false;
    }
  }

  /**
   * JSONファイルからデータをインポート
   * @param {File} file - インポートするファイル
   * @param {string} type - 'knowledge' または 'questions'
   * @returns {Promise<boolean>} 成功したかどうか
   */
  async importData(file, type = 'knowledge') {
    return new Promise((resolve, reject) => {
      try {
        const reader = new FileReader();

        reader.onload = (e) => {
          try {
            const data = JSON.parse(e.target.result);

            if (!Array.isArray(data)) {
              throw new Error('Invalid data format: expected array');
            }

            let success;
            if (type === 'knowledge') {
              success = this.saveAllKnowledge(data);
            } else if (type === 'questions') {
              success = this.saveAllQuestions(data);
            } else {
              throw new Error('Invalid import type');
            }

            resolve(success);
          } catch (error) {
            console.error('Failed to parse imported data:', error);
            reject(error);
          }
        };

        reader.onerror = () => {
          reject(new Error('Failed to read file'));
        };

        reader.readAsText(file);
      } catch (error) {
        console.error('Failed to import data:', error);
        reject(error);
      }
    });
  }

  /**
   * 全てのデータをクリア
   * @param {string} type - 'all', 'knowledge', 'questions', 'settings'
   * @returns {boolean} 成功したかどうか
   */
  clearData(type = 'all') {
    try {
      if (type === 'all' || type === 'knowledge') {
        localStorage.removeItem(this.STORAGE_KEY_KNOWLEDGE);
      }
      if (type === 'all' || type === 'questions') {
        localStorage.removeItem(this.STORAGE_KEY_QUESTIONS);
      }
      if (type === 'all' || type === 'settings') {
        localStorage.removeItem(this.STORAGE_KEY_SETTINGS);
      }
      return true;
    } catch (error) {
      console.error('Failed to clear data:', error);
      return false;
    }
  }

  /**
   * ストレージの使用状況を取得
   * @returns {Object} 使用状況の情報
   */
  getStorageInfo() {
    try {
      const knowledge = this.getAllKnowledge();
      const questions = this.getAllQuestions();
      const settings = this.getSettings();

      const knowledgeSize = new Blob([JSON.stringify(knowledge)]).size;
      const questionsSize = new Blob([JSON.stringify(questions)]).size;
      const settingsSize = new Blob([JSON.stringify(settings)]).size;
      const totalSize = knowledgeSize + questionsSize + settingsSize;

      return {
        knowledgeCount: knowledge.length,
        questionsCount: questions.length,
        knowledgeSize: this._formatBytes(knowledgeSize),
        questionsSize: this._formatBytes(questionsSize),
        settingsSize: this._formatBytes(settingsSize),
        totalSize: this._formatBytes(totalSize),
        totalSizeBytes: totalSize
      };
    } catch (error) {
      console.error('Failed to get storage info:', error);
      return null;
    }
  }

  // ==================== Private Methods ====================

  /**
   * ユニークIDを生成
   * @returns {string} ID
   */
  _generateId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 日付文字列を生成（YYYYMMDD形式）
   * @returns {string} 日付文字列
   */
  _getDateString() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}${month}${day}`;
  }

  /**
   * バイト数を人間が読める形式に変換
   * @param {number} bytes - バイト数
   * @returns {string} フォーマットされた文字列
   */
  _formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * デフォルト設定を取得
   * @returns {Object} デフォルト設定
   */
  _getDefaultSettings() {
    return {
      theme: 'light',
      itemsPerPage: 10,
      autoSave: true,
      enableNotifications: true,
      language: 'ja'
    };
  }
}

// グローバルインスタンスをエクスポート
const storageManager = new StorageManager();
