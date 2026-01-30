#!/bin/bash
# ==================================================
# Mirai IT Knowledge System - Systemd Service Installer
# systemdサービスインストール/アンインストールスクリプト
# ==================================================

set -e

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# プロジェクトルート
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SYSTEMD_DIR="/etc/systemd/system"

# サービス名
DEV_SERVICE="mirai-knowledge-dev"
PROD_SERVICE="mirai-knowledge-prod"

# ヘルプ表示
function show_help() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${GREEN}Mirai IT Knowledge System${NC}"
    echo -e "${GREEN}Systemd Service Installer${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}使用方法:${NC}"
    echo -e "  $0 [コマンド] [オプション]"
    echo ""
    echo -e "${YELLOW}コマンド:${NC}"
    echo -e "  ${BLUE}install${NC}      サービスをインストール"
    echo -e "  ${BLUE}uninstall${NC}    サービスをアンインストール"
    echo -e "  ${BLUE}status${NC}       サービス状態を表示"
    echo -e "  ${BLUE}logs${NC}         サービスログを表示"
    echo -e "  ${BLUE}validate${NC}     サービスファイルを検証"
    echo ""
    echo -e "${YELLOW}オプション:${NC}"
    echo -e "  ${BLUE}--dev${NC}        開発環境のみ"
    echo -e "  ${BLUE}--prod${NC}       本番環境のみ"
    echo -e "  ${BLUE}--help${NC}       このヘルプを表示"
    echo ""
    echo -e "${YELLOW}例:${NC}"
    echo -e "  sudo $0 install           # 両環境をインストール"
    echo -e "  sudo $0 install --dev     # 開発環境のみ"
    echo -e "  sudo $0 status            # 状態確認"
    echo -e "  $0 logs --prod            # 本番ログ表示"
    echo ""
}

# root権限確認
function check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ このコマンドはroot権限で実行する必要があります${NC}"
        echo -e "${YELLOW}以下のコマンドで実行してください:${NC}"
        echo -e "${BLUE}   sudo $0 $@${NC}"
        exit 1
    fi
}

# サービスファイル検証
function validate_service() {
    local service_file="$1"
    local service_name="$2"

    echo -e "${BLUE}🔍 検証中: ${service_name}${NC}"

    if [ ! -f "$service_file" ]; then
        echo -e "${RED}   ❌ ファイルが存在しません: ${service_file}${NC}"
        return 1
    fi

    # systemd-analyze verify（利用可能な場合）
    if command -v systemd-analyze &> /dev/null; then
        if systemd-analyze verify "$service_file" 2>&1 | grep -q "Error\|error"; then
            echo -e "${RED}   ❌ 検証エラー:${NC}"
            systemd-analyze verify "$service_file" 2>&1 | head -10
            return 1
        fi
    fi

    # 基本的な構文チェック
    if ! grep -q "^\[Unit\]" "$service_file"; then
        echo -e "${RED}   ❌ [Unit] セクションがありません${NC}"
        return 1
    fi

    if ! grep -q "^\[Service\]" "$service_file"; then
        echo -e "${RED}   ❌ [Service] セクションがありません${NC}"
        return 1
    fi

    if ! grep -q "^\[Install\]" "$service_file"; then
        echo -e "${RED}   ❌ [Install] セクションがありません${NC}"
        return 1
    fi

    echo -e "${GREEN}   ✅ 検証OK${NC}"
    return 0
}

# サービスインストール
function install_service() {
    local service_name="$1"
    local service_file="$SCRIPT_DIR/systemd/${service_name}.service"

    echo -e "${BLUE}📦 インストール中: ${service_name}${NC}"

    # 検証
    if ! validate_service "$service_file" "$service_name"; then
        echo -e "${RED}   ❌ インストール中止${NC}"
        return 1
    fi

    # 既存サービスのバックアップ
    if [ -f "$SYSTEMD_DIR/${service_name}.service" ]; then
        local backup_file="$SYSTEMD_DIR/${service_name}.service.bak.$(date +%Y%m%d_%H%M%S)"
        cp "$SYSTEMD_DIR/${service_name}.service" "$backup_file"
        echo -e "${YELLOW}   ⚠️  既存ファイルをバックアップ: ${backup_file}${NC}"
    fi

    # コピー
    cp "$service_file" "$SYSTEMD_DIR/"
    echo -e "${GREEN}   ✅ サービスファイルをコピー${NC}"

    return 0
}

# サービスアンインストール
function uninstall_service() {
    local service_name="$1"

    echo -e "${BLUE}🗑️  アンインストール中: ${service_name}${NC}"

    # サービス停止
    if systemctl is-active --quiet "${service_name}.service" 2>/dev/null; then
        systemctl stop "${service_name}.service"
        echo -e "${YELLOW}   ⏹️  サービスを停止${NC}"
    fi

    # 自動起動無効化
    if systemctl is-enabled --quiet "${service_name}.service" 2>/dev/null; then
        systemctl disable "${service_name}.service"
        echo -e "${YELLOW}   🔓 自動起動を無効化${NC}"
    fi

    # ファイル削除
    if [ -f "$SYSTEMD_DIR/${service_name}.service" ]; then
        rm "$SYSTEMD_DIR/${service_name}.service"
        echo -e "${GREEN}   ✅ サービスファイルを削除${NC}"
    else
        echo -e "${YELLOW}   ⚠️  サービスファイルが存在しません${NC}"
    fi

    return 0
}

# サービス状態表示
function show_status() {
    local service_name="$1"

    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 ${service_name}${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if systemctl list-unit-files "${service_name}.service" &>/dev/null; then
        # 基本状態
        local active=$(systemctl is-active "${service_name}.service" 2>/dev/null || echo "unknown")
        local enabled=$(systemctl is-enabled "${service_name}.service" 2>/dev/null || echo "unknown")

        case "$active" in
            active)
                echo -e "  状態: ${GREEN}● 実行中${NC}"
                ;;
            inactive)
                echo -e "  状態: ${YELLOW}○ 停止${NC}"
                ;;
            failed)
                echo -e "  状態: ${RED}✗ 失敗${NC}"
                ;;
            *)
                echo -e "  状態: ${YELLOW}? 不明${NC}"
                ;;
        esac

        case "$enabled" in
            enabled)
                echo -e "  自動起動: ${GREEN}有効${NC}"
                ;;
            disabled)
                echo -e "  自動起動: ${YELLOW}無効${NC}"
                ;;
            *)
                echo -e "  自動起動: ${YELLOW}未設定${NC}"
                ;;
        esac

        # 詳細情報（実行中の場合）
        if [ "$active" = "active" ]; then
            local pid=$(systemctl show "${service_name}.service" --property=MainPID --value 2>/dev/null)
            local memory=$(systemctl show "${service_name}.service" --property=MemoryCurrent --value 2>/dev/null)

            [ -n "$pid" ] && [ "$pid" != "0" ] && echo -e "  PID: ${pid}"
            [ -n "$memory" ] && [ "$memory" != "[not set]" ] && echo -e "  メモリ: $(numfmt --to=iec $memory 2>/dev/null || echo $memory)"
        fi
    else
        echo -e "  ${YELLOW}⚠️  インストールされていません${NC}"
    fi
}

# ログ表示
function show_logs() {
    local service_name="$1"
    local lines="${2:-50}"

    echo -e "${BLUE}📋 ${service_name} ログ (最新${lines}行)${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    journalctl -u "${service_name}.service" -n "$lines" --no-pager
}

# メイン処理
COMMAND="${1:-help}"
TARGET="both"  # both, dev, prod

# オプション解析
shift || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dev)
            TARGET="dev"
            shift
            ;;
        --prod)
            TARGET="prod"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

case "$COMMAND" in
    install)
        check_root
        echo -e "${CYAN}========================================${NC}"
        echo -e "${GREEN}🔧 Systemdサービスインストール${NC}"
        echo -e "${CYAN}========================================${NC}\n"

        if [ "$TARGET" = "both" ] || [ "$TARGET" = "dev" ]; then
            install_service "$DEV_SERVICE"
        fi

        if [ "$TARGET" = "both" ] || [ "$TARGET" = "prod" ]; then
            install_service "$PROD_SERVICE"
        fi

        # systemdリロード
        echo -e "\n${BLUE}🔄 systemdをリロード中...${NC}"
        systemctl daemon-reload
        echo -e "${GREEN}✅ systemdリロード完了${NC}"

        # サービス有効化
        echo -e "\n${BLUE}🔧 サービスを有効化中...${NC}"
        if [ "$TARGET" = "both" ] || [ "$TARGET" = "dev" ]; then
            systemctl enable "${DEV_SERVICE}.service"
            echo -e "${GREEN}✅ ${DEV_SERVICE} を有効化${NC}"
        fi
        if [ "$TARGET" = "both" ] || [ "$TARGET" = "prod" ]; then
            systemctl enable "${PROD_SERVICE}.service"
            echo -e "${GREEN}✅ ${PROD_SERVICE} を有効化${NC}"
        fi

        # 状態表示
        if [ "$TARGET" = "both" ] || [ "$TARGET" = "dev" ]; then
            show_status "$DEV_SERVICE"
        fi
        if [ "$TARGET" = "both" ] || [ "$TARGET" = "prod" ]; then
            show_status "$PROD_SERVICE"
        fi

        echo -e "\n${CYAN}========================================${NC}"
        echo -e "${GREEN}✅ インストール完了！${NC}"
        echo -e "${CYAN}========================================${NC}"
        echo -e "\n${YELLOW}サービス操作コマンド:${NC}"
        echo -e "  ${BLUE}sudo systemctl start ${DEV_SERVICE}${NC}   # 開発環境起動"
        echo -e "  ${BLUE}sudo systemctl start ${PROD_SERVICE}${NC}  # 本番環境起動"
        echo -e "  ${BLUE}sudo systemctl stop <service>${NC}         # 停止"
        echo -e "  ${BLUE}sudo systemctl restart <service>${NC}      # 再起動"
        echo -e "  ${BLUE}sudo journalctl -u <service> -f${NC}       # ログ監視"
        ;;

    uninstall)
        check_root
        echo -e "${CYAN}========================================${NC}"
        echo -e "${RED}🗑️  Systemdサービスアンインストール${NC}"
        echo -e "${CYAN}========================================${NC}\n"

        read -p "本当にアンインストールしますか？ (y/N): " confirm
        if [[ ! "$confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            echo -e "${YELLOW}キャンセルしました${NC}"
            exit 0
        fi

        if [ "$TARGET" = "both" ] || [ "$TARGET" = "dev" ]; then
            uninstall_service "$DEV_SERVICE"
        fi

        if [ "$TARGET" = "both" ] || [ "$TARGET" = "prod" ]; then
            uninstall_service "$PROD_SERVICE"
        fi

        systemctl daemon-reload
        echo -e "\n${GREEN}✅ アンインストール完了${NC}"
        ;;

    status)
        if [ "$TARGET" = "both" ] || [ "$TARGET" = "dev" ]; then
            show_status "$DEV_SERVICE"
        fi
        if [ "$TARGET" = "both" ] || [ "$TARGET" = "prod" ]; then
            show_status "$PROD_SERVICE"
        fi
        ;;

    logs)
        if [ "$TARGET" = "dev" ]; then
            show_logs "$DEV_SERVICE"
        elif [ "$TARGET" = "prod" ]; then
            show_logs "$PROD_SERVICE"
        else
            show_logs "$DEV_SERVICE"
            echo ""
            show_logs "$PROD_SERVICE"
        fi
        ;;

    validate)
        echo -e "${CYAN}========================================${NC}"
        echo -e "${BLUE}🔍 サービスファイル検証${NC}"
        echo -e "${CYAN}========================================${NC}\n"

        if [ "$TARGET" = "both" ] || [ "$TARGET" = "dev" ]; then
            validate_service "$SCRIPT_DIR/systemd/${DEV_SERVICE}.service" "$DEV_SERVICE"
        fi
        if [ "$TARGET" = "both" ] || [ "$TARGET" = "prod" ]; then
            validate_service "$SCRIPT_DIR/systemd/${PROD_SERVICE}.service" "$PROD_SERVICE"
        fi
        ;;

    help|--help|-h)
        show_help
        ;;

    *)
        echo -e "${RED}❌ 不明なコマンド: ${COMMAND}${NC}"
        show_help
        exit 1
        ;;
esac
