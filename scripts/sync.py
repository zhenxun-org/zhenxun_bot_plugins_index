import argparse
import contextlib
import json
import sys
import urllib.parse
from typing import Dict, Optional

import requests


def get_repository_info(
    token: str, organization_id: str, namespace_path: str, repo_name: str
) -> Optional[Dict]:
    """获取代码库信息，通过URL-Encoder编码的全路径查询"""

    # 构造全路径：组织ID/命名空间路径/仓库名称
    full_path = f"{organization_id}/{namespace_path}/{repo_name}"

    # URL编码全路径
    encoded_full_path = urllib.parse.quote(full_path, safe="")

    # 构建查询URL
    url = f"https://openapi-rdc.aliyuncs.com/oapi/v1/codeup/organizations/{organization_id}/repositories/{encoded_full_path}"

    headers = {"Content-Type": "application/json", "x-yunxiao-token": token}

    try:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            repo_info = response.json()
            print(f"ℹ️ 找到已存在的代码库: {repo_name} (ID: {repo_info.get('id')})")
            return repo_info
        elif response.status_code == 404:
            print(f"ℹ️ 代码库不存在: {repo_name}")
            return None
        else:
            print(f"❌ 查询代码库失败，状态码: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print("❌ 查询请求超时")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到服务接入点")
        return None
    except Exception as error:
        print(f"❌ 查询代码库失败: {str(error)}")
        return None


def create_repository(
    token: str,
    organization_id: str,
    namespace_id: int,
    repo_name: str,
    description: str = "",
    visibility: str = "internal",
) -> bool:
    """创建阿里云代码库"""

    # 构建请求URL
    url = f"https://openapi-rdc.aliyuncs.com/oapi/v1/codeup/organizations/{organization_id}/repositories"

    # 构建请求头
    headers = {"Content-Type": "application/json", "x-yunxiao-token": token}

    # 构建请求体 - 根据API文档，不需要path参数
    payload = {
        "name": repo_name,
        "namespaceId": namespace_id,
        "visibility": visibility,
        "organizationId": organization_id,
        "path": repo_name,
    }

    # 如果有描述，则添加
    if description:
        payload["description"] = description

    # 添加查询参数，自动创建父路径
    params = {"createParentPath": "true"}

    print(f"🔄 正在创建代码库: {repo_name}")
    print(f"   组织ID: {organization_id}")
    print(f"   命名空间ID: {namespace_id}")

    try:
        print("正在请求创建仓库，参数 -> payload: ", payload, "params: ", params)
        response = requests.post(
            url, headers=headers, params=params, json=payload, timeout=30
        )

        if response.status_code in {200, 201}:
            return _extracted_from_create_repository_43(response, repo_name)
        elif response.status_code == 409:
            # 仓库已存在
            print(f"ℹ️ 代码库已存在: {repo_name}")
            return True

        elif response.status_code == 401:
            print("❌ 认证失败: 请检查个人访问令牌是否正确")
            return False

        elif response.status_code == 403:
            print("❌ 权限不足: 请确认有创建代码库的权限")
            return False

        else:
            # 其他错误
            error_msg = f"创建失败，状态码: {response.status_code}"
            with contextlib.suppress(Exception):
                error_data = response.json()
                if "message" in error_data:
                    error_msg = error_data["message"]
            print(f"❌ {error_msg}")
            return False

    except requests.exceptions.Timeout:
        print("❌ 请求超时: 创建代码库操作超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到服务接入点")
        return False
    except Exception as error:
        print(f"❌ 创建代码库失败: {str(error)}")
        return False


# TODO Rename this here and in `create_repository`
def _extracted_from_create_repository_43(response, repo_name):
    # 创建成功
    repo_data = response.json()
    print(f"✅ 代码库创建成功: {repo_name}")
    print(f"   代码库ID: {repo_data.get('id', 'N/A')}")
    print(f"   完整路径: {repo_data.get('pathWithNamespace', 'N/A')}")
    print(f"   Web URL: {repo_data.get('webUrl', 'N/A')}")
    return True


def main():
    """主函数"""
    # 设置命令行参数解析器
    parser = argparse.ArgumentParser(description="创建阿里云Codeup代码库")

    # 添加所有必要的参数
    parser.add_argument(
        "--changed-plugins", type=str, required=True, help="JSON格式的变更插件列表"
    )
    parser.add_argument("--org-id", type=str, required=True, help="阿里云组织ID")
    parser.add_argument(
        "--access-token", type=str, required=True, help="个人访问令牌 (x-yunxiao-token)"
    )
    parser.add_argument(
        "--namespace-id", type=int, default=1638483, help="命名空间ID，默认为1638483"
    )
    parser.add_argument(
        "--namespace-path",
        type=str,
        default="zhenxun_plugins",
        help="命名空间路径，默认为zhenxun_plugins",
    )
    parser.add_argument(
        "--visibility",
        type=str,
        default="internal",
        choices=["private", "internal", "public"],
        help="代码库可见性",
    )
    parser.add_argument("--skip-check", action="store_true", help="跳过检查直接创建")

    args = parser.parse_args()

    print("=" * 50)
    print("阿里云代码库创建任务开始")
    print("服务接入点: openapi-rdc.aliyuncs.com")
    print(f"组织ID: {args.org_id}")
    print(f"命名空间ID: {args.namespace_id}")
    print(f"命名空间路径: {args.namespace_path}")
    print("=" * 50)

    try:
        # 解析变更插件数据
        try:
            changed_plugins = json.loads(args.changed_plugins)
        except json.JSONDecodeError as e:
            raise ValueError(f"解析变更插件列表失败: {str(e)}")

        # 如果没有变更，直接退出
        if not changed_plugins:
            print("ℹ️ 没有检测到插件变更，无需创建")
            return

        print(f"检测到 {len(changed_plugins)} 个需要处理的代码库")

        results = []
        created_count = 0
        existing_count = 0

        for plugin in changed_plugins:
            repo_name = plugin["repo_name"]
            github_url = plugin["github_url"]
            plugin_name = plugin.get("name", repo_name)

            print("\n" + "-" * 50)
            print(f"🔄 处理插件: {plugin_name}")
            print(f"代码库名称: {repo_name}")
            print(f"GitHub 地址: {github_url}")
            print("-" * 50)

            # 构建描述信息
            description = f"{plugin_name}\n\n原始GitHub地址: {github_url}"
            if "description" in plugin:
                description = f"{plugin['description']}\n\n原始GitHub地址: {github_url}"

            try:
                # 先检查代码库是否已存在
                repo_exists = False
                if not args.skip_check:
                    repo_info = get_repository_info(
                        token=args.access_token,
                        organization_id=args.org_id,
                        namespace_path=args.namespace_path,
                        repo_name=repo_name,
                    )

                    if repo_info:
                        repo_exists = True
                        print(f"ℹ️ 代码库已存在，跳过创建: {repo_name}")

                # 如果不存在或跳过检查，则尝试创建
                if not repo_exists:
                    success = create_repository(
                        token=args.access_token,
                        organization_id=args.org_id,
                        namespace_id=args.namespace_id,
                        repo_name=repo_name,
                        description=description,
                        visibility=args.visibility,
                    )

                    if success:
                        results.append(
                            {
                                "name": plugin_name,
                                "repo_name": repo_name,
                                "github_url": github_url,
                                "status": "created",
                                "message": "代码库创建成功",
                            }
                        )
                        created_count += 1
                    else:
                        results.append(
                            {
                                "name": plugin_name,
                                "repo_name": repo_name,
                                "github_url": github_url,
                                "status": "failed",
                                "message": "代码库创建失败",
                            }
                        )
                else:
                    results.append(
                        {
                            "name": plugin_name,
                            "repo_name": repo_name,
                            "github_url": github_url,
                            "status": "existing",
                            "message": "代码库已存在",
                        }
                    )
                    existing_count += 1

            except Exception as e:
                print(f"❌ 处理 {repo_name} 时发生错误: {str(e)}")
                results.append(
                    {
                        "name": plugin_name,
                        "repo_name": repo_name,
                        "github_url": github_url,
                        "status": "error",
                        "error": str(e),
                    }
                )

        _extracted_from_main_148("代码库创建任务完成")
        print(f"总计处理: {len(results)} 个代码库")
        print(f"成功创建: {created_count} 个")
        print(f"已存在: {existing_count} 个")

        failed_count = len([r for r in results if r["status"] in ["failed", "error"]])
        print(f"失败: {failed_count} 个")

        # 将结果写入文件
        with open("repository_results.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": {
                        "total": len(results),
                        "created": created_count,
                        "existing": existing_count,
                        "failed": failed_count,
                    },
                    "details": results,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print("\n✅ 详细结果已保存到 repository_results.json")

        # 如果有失败的任务，返回非零退出码
        if any(r["status"] in ["failed", "error"] for r in results):
            print("❌ 部分代码库处理失败")
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        _extracted_from_main_148("❌ 发生严重错误")
        print(f"错误信息: {str(e)}")
        print(f"错误类型: {type(e).__name__}")

        # 写入错误结果
        with open("repository_results.json", "w", encoding="utf-8") as f:
            json.dump(
                {"status": "error", "error": str(e), "error_type": type(e).__name__},
                f,
                ensure_ascii=False,
            )

        sys.exit(1)


# TODO Rename this here and in `main`
def _extracted_from_main_148(arg0):
    # 输出处理结果
    print("\n" + "=" * 50)
    print(arg0)
    print("=" * 50)


if __name__ == "__main__":
    main()
