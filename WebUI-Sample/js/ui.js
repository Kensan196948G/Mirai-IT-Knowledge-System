/**
 * UI Utilities
 * UI操作ユーティリティ（エスケープ、日付フォーマット、通知表示）
 */

class UIUtils {
  /**
   * HTMLエスケープ
   * @param {string} text - エスケープするテキスト
   * @returns {string} エスケープされたテキスト
   */
  static escapeHtml(text) {
    if (!text) return '';

    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * HTMLアンエスケープ
   * @param {string} html - アンエスケープするHTML
   * @returns {string} アンエスケープされたテキスト
   */
  static unescapeHtml(html) {
    if (!html) return '';

    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent;
  }

  /**
   * 日付を相対的な形式でフォーマット（例: "2時間前"）
   * @param {string|Date} date - 日付
   * @returns {string} フォーマットされた日付文字列
   */
  static formatRelativeTime(date) {
    try {
      const now = new Date();
      const target = new Date(date);
      const diffMs = now - target;
      const diffSec = Math.floor(diffMs / 1000);
      const diffMin = Math.floor(diffSec / 60);
      const diffHour = Math.floor(diffMin / 60);
      const diffDay = Math.floor(diffHour / 24);
      const diffMonth = Math.floor(diffDay / 30);
      const diffYear = Math.floor(diffDay / 365);

      if (diffSec < 60) {
        return 'たった今';
      } else if (diffMin < 60) {
        return `${diffMin}分前`;
      } else if (diffHour < 24) {
        return `${diffHour}時間前`;
      } else if (diffDay < 30) {
        return `${diffDay}日前`;
      } else if (diffMonth < 12) {
        return `${diffMonth}ヶ月前`;
      } else {
        return `${diffYear}年前`;
      }
    } catch (error) {
      console.error('Failed to format relative time:', error);
      return '';
    }
  }

  /**
   * 日付を標準形式でフォーマット（例: "2026-01-20 15:30:45"）
   * @param {string|Date} date - 日付
   * @param {boolean} includeTime - 時刻を含めるか
   * @returns {string} フォーマットされた日付文字列
   */
  static formatDateTime(date, includeTime = true) {
    try {
      const d = new Date(date);
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');

      if (!includeTime) {
        return `${year}-${month}-${day}`;
      }

      const hour = String(d.getHours()).padStart(2, '0');
      const minute = String(d.getMinutes()).padStart(2, '0');
      const second = String(d.getSeconds()).padStart(2, '0');

      return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
    } catch (error) {
      console.error('Failed to format date time:', error);
      return '';
    }
  }

  /**
   * 日付を日本語形式でフォーマット（例: "2026年1月20日"）
   * @param {string|Date} date - 日付
   * @returns {string} フォーマットされた日付文字列
   */
  static formatJapaneseDate(date) {
    try {
      const d = new Date(date);
      const year = d.getFullYear();
      const month = d.getMonth() + 1;
      const day = d.getDate();

      return `${year}年${month}月${day}日`;
    } catch (error) {
      console.error('Failed to format Japanese date:', error);
      return '';
    }
  }

  /**
   * 通知を表示
   * @param {string} message - メッセージ
   * @param {string} type - タイプ（success, error, warning, info）
   * @param {number} duration - 表示時間（ミリ秒、0で自動消去なし）
   */
  static showNotification(message, type = 'info', duration = 3000) {
    try {
      // 既存の通知コンテナを取得または作成
      let container = document.getElementById('notification-container');
      if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
      }

      // 通知要素を作成
      const notification = document.createElement('div');
      notification.className = `notification notification-${type}`;
      notification.innerHTML = `
        <div class="notification-content">
          <span class="notification-icon">${this._getNotificationIcon(type)}</span>
          <span class="notification-message">${this.escapeHtml(message)}</span>
          <button class="notification-close" aria-label="閉じる">&times;</button>
        </div>
      `;

      // 閉じるボタンのイベント
      const closeBtn = notification.querySelector('.notification-close');
      closeBtn.addEventListener('click', () => {
        this._removeNotification(notification);
      });

      // コンテナに追加
      container.appendChild(notification);

      // アニメーション
      setTimeout(() => {
        notification.classList.add('notification-show');
      }, 10);

      // 自動消去
      if (duration > 0) {
        setTimeout(() => {
          this._removeNotification(notification);
        }, duration);
      }
    } catch (error) {
      console.error('Failed to show notification:', error);
    }
  }

  /**
   * 通知を削除
   * @param {HTMLElement} notification - 通知要素
   */
  static _removeNotification(notification) {
    notification.classList.remove('notification-show');
    notification.classList.add('notification-hide');
    setTimeout(() => {
      notification.remove();
    }, 300);
  }

  /**
   * 通知アイコンを取得
   * @param {string} type - タイプ
   * @returns {string} アイコン
   */
  static _getNotificationIcon(type) {
    const icons = {
      success: '✓',
      error: '✗',
      warning: '⚠',
      info: 'ℹ'
    };
    return icons[type] || icons.info;
  }

  /**
   * 確認ダイアログを表示
   * @param {string} message - メッセージ
   * @param {Function} onConfirm - 確認時のコールバック
   * @param {Function} onCancel - キャンセル時のコールバック
   */
  static showConfirm(message, onConfirm, onCancel = null) {
    try {
      // モーダル背景を作成
      const overlay = document.createElement('div');
      overlay.className = 'modal-overlay';

      // モーダルを作成
      const modal = document.createElement('div');
      modal.className = 'modal modal-confirm';
      modal.innerHTML = `
        <div class="modal-content">
          <div class="modal-header">
            <h3>確認</h3>
          </div>
          <div class="modal-body">
            <p>${this.escapeHtml(message)}</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" data-action="cancel">キャンセル</button>
            <button class="btn btn-primary" data-action="confirm">OK</button>
          </div>
        </div>
      `;

      overlay.appendChild(modal);
      document.body.appendChild(overlay);

      // イベントハンドラ
      const confirmBtn = modal.querySelector('[data-action="confirm"]');
      const cancelBtn = modal.querySelector('[data-action="cancel"]');

      const cleanup = () => {
        overlay.remove();
      };

      confirmBtn.addEventListener('click', () => {
        cleanup();
        if (onConfirm) onConfirm();
      });

      cancelBtn.addEventListener('click', () => {
        cleanup();
        if (onCancel) onCancel();
      });

      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          cleanup();
          if (onCancel) onCancel();
        }
      });

      // アニメーション
      setTimeout(() => {
        overlay.classList.add('modal-show');
      }, 10);
    } catch (error) {
      console.error('Failed to show confirm dialog:', error);
    }
  }

  /**
   * ローディングスピナーを表示
   * @param {string} message - メッセージ（オプション）
   * @returns {HTMLElement} スピナー要素
   */
  static showLoading(message = '読み込み中...') {
    try {
      const overlay = document.createElement('div');
      overlay.className = 'loading-overlay';
      overlay.innerHTML = `
        <div class="loading-spinner">
          <div class="spinner"></div>
          <p class="loading-message">${this.escapeHtml(message)}</p>
        </div>
      `;

      document.body.appendChild(overlay);

      setTimeout(() => {
        overlay.classList.add('loading-show');
      }, 10);

      return overlay;
    } catch (error) {
      console.error('Failed to show loading:', error);
      return null;
    }
  }

  /**
   * ローディングスピナーを非表示
   * @param {HTMLElement} spinner - スピナー要素
   */
  static hideLoading(spinner) {
    if (!spinner) return;

    try {
      spinner.classList.remove('loading-show');
      setTimeout(() => {
        spinner.remove();
      }, 300);
    } catch (error) {
      console.error('Failed to hide loading:', error);
    }
  }

  /**
   * テキストをハイライト
   * @param {string} text - テキスト
   * @param {string} query - ハイライトするクエリ
   * @returns {string} ハイライトされたHTML
   */
  static highlightText(text, query) {
    if (!text || !query) return this.escapeHtml(text);

    const escapedText = this.escapeHtml(text);
    const escapedQuery = this.escapeHtml(query);

    const regex = new RegExp(`(${escapedQuery})`, 'gi');
    return escapedText.replace(regex, '<mark>$1</mark>');
  }

  /**
   * MarkdownをシンプルなHTMLに変換（基本的な対応のみ）
   * @param {string} markdown - Markdownテキスト
   * @returns {string} HTML
   */
  static markdownToHtml(markdown) {
    if (!markdown) return '';

    let html = this.escapeHtml(markdown);

    // 見出し
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // 太字
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');

    // イタリック
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.*?)_/g, '<em>$1</em>');

    // リスト
    html = html.replace(/^\* (.*$)/gim, '<li>$1</li>');
    html = html.replace(/^- (.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // リンク
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

    // 改行
    html = html.replace(/\n/g, '<br>');

    return html;
  }

  /**
   * バイト数を人間が読める形式に変換
   * @param {number} bytes - バイト数
   * @returns {string} フォーマットされた文字列
   */
  static formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * 数値にカンマ区切りを追加
   * @param {number} num - 数値
   * @returns {string} フォーマットされた文字列
   */
  static formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  /**
   * ITSMタイプのバッジHTMLを生成
   * @param {string} itsmType - ITSMタイプ
   * @returns {string} バッジHTML
   */
  static getItsmTypeBadge(itsmType) {
    const badges = {
      Incident: '<span class="badge badge-incident">インシデント</span>',
      Problem: '<span class="badge badge-problem">問題管理</span>',
      Change: '<span class="badge badge-change">変更管理</span>',
      Release: '<span class="badge badge-release">リリース</span>',
      Request: '<span class="badge badge-request">リクエスト</span>',
      Other: '<span class="badge badge-other">その他</span>'
    };
    return badges[itsmType] || badges.Other;
  }

  /**
   * 重要度のバッジHTMLを生成
   * @param {string} severity - 重要度
   * @returns {string} バッジHTML
   */
  static getSeverityBadge(severity) {
    const badges = {
      critical: '<span class="badge badge-critical">緊急</span>',
      high: '<span class="badge badge-high">高</span>',
      medium: '<span class="badge badge-medium">中</span>',
      low: '<span class="badge badge-low">低</span>'
    };
    return badges[severity] || '';
  }

  /**
   * ステータスのバッジHTMLを生成
   * @param {string} status - ステータス
   * @returns {string} バッジHTML
   */
  static getStatusBadge(status) {
    const badges = {
      resolved: '<span class="badge badge-resolved">解決済み</span>',
      'in-progress': '<span class="badge badge-in-progress">進行中</span>',
      pending: '<span class="badge badge-pending">保留中</span>',
      scheduled: '<span class="badge badge-scheduled">予定</span>',
      approved: '<span class="badge badge-approved">承認済み</span>',
      completed: '<span class="badge badge-completed">完了</span>'
    };
    return badges[status] || '';
  }

  /**
   * テキストを切り詰める
   * @param {string} text - テキスト
   * @param {number} maxLength - 最大長
   * @param {string} suffix - サフィックス
   * @returns {string} 切り詰められたテキスト
   */
  static truncate(text, maxLength = 100, suffix = '...') {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + suffix;
  }

  /**
   * クリップボードにコピー
   * @param {string} text - コピーするテキスト
   * @returns {Promise<boolean>} 成功したかどうか
   */
  static async copyToClipboard(text) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
        return true;
      } else {
        // フォールバック
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        const success = document.execCommand('copy');
        document.body.removeChild(textarea);
        return success;
      }
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      return false;
    }
  }

  /**
   * デバウンス関数
   * @param {Function} func - 実行する関数
   * @param {number} delay - 遅延時間（ミリ秒）
   * @returns {Function} デバウンスされた関数
   */
  static debounce(func, delay = 300) {
    let timeoutId;
    return function (...args) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        func.apply(this, args);
      }, delay);
    };
  }

  /**
   * スロットル関数
   * @param {Function} func - 実行する関数
   * @param {number} limit - 制限時間（ミリ秒）
   * @returns {Function} スロットルされた関数
   */
  static throttle(func, limit = 300) {
    let inThrottle;
    return function (...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => {
          inThrottle = false;
        }, limit);
      }
    };
  }
}

// グローバルにエクスポート
window.UIUtils = UIUtils;
