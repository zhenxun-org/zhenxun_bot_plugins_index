import json
import os
import subprocess
import sys
import argparse
import tempfile
import shutil
from alibabacloud_devops20210625.client import Client as devops20210625Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_devops20210625 import models as devops_20210625_models
from alibabacloud_tea_util import models as util_models


def get_client(access_key_id, access_key_secret) -> devops20210625Client:
    """获取阿里云客户端"""
    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        endpoint="devops.cn-hangzhou.aliyuncs.com",
        region_id="cn-hangzhou",
    )
    return devops20210625Client(config)


def create_repository(client, org_id, repo_name):
    """创建阿里云仓库"""
    request = devops_20210625_models.CreateRepositoryRequest(
        namespace_id=1638483,
        name=repo_name,
        visibility_level=10,
        organization_id=org_id,
        readmeType="EMPTY",
    )
    runtime = util_models.RuntimeOptions()
    try:
        client.create_repository_with_options(request, headers={}, runtime=runtime)
        print(f"✅ 仓库创建成功: {repo_name}")
        return True
    except Exception as error:
        # 更健壮的仓库存在检测
        error_msg = str(error)
        if "Repository already exists" in error_msg or "已存在" in error_msg:
            print(f"ℹ️ 仓库已存在: {repo_name}")
            return True
        print(f"❌ 仓库创建失败 {repo_name}: {error_msg}")
        return False


def sync_repository_import_method(github_url, repo_name, auth_url):
    """使用导入代码库的方式同步（阿里云推荐方式）"""
    try:
        # 使用临时目录来操作
        temp_dir = tempfile.mkdtemp(prefix=f"{repo_name}_sync_")
        bare_dir = os.path.join(temp_dir, f"{repo_name}.git")

        print(f"🔄 使用导入代码库方式同步: {github_url}")
        print(f"临时目录: {temp_dir}")

        # 步骤1: 克隆裸仓库
        print("🔄 克隆裸仓库...")
        subprocess.run(
            ["git", "clone", "--bare", github_url, bare_dir],
            check=True,
            capture_output=True,
            text=True,
        )

        # 进入裸仓库目录
        os.chdir(bare_dir)

        # 步骤2: 设置阿里云远程仓库地址
        print("🔄 设置阿里云远程仓库地址...")
        subprocess.run(
            ["git", "remote", "set-url", "origin", auth_url],
            check=True,
            capture_output=True,
            text=True,
        )

        # 步骤3: 推送所有标签和分支
        print("🔄 推送标签和分支到阿里云...")

        # 先推送标签
        tag_result = subprocess.run(
            ["git", "push", "origin", "--tags"],
            capture_output=True,
            text=True,
        )

        # 再推送所有分支
        branch_result = subprocess.run(
            ["git", "push", "origin", "--all"],
            capture_output=True,
            text=True,
        )

        # 检查推送结果
        if tag_result.returncode != 0 and branch_result.returncode != 0:
            error_msg = ""
            if tag_result.stderr:
                error_msg += f"标签推送失败: {tag_result.stderr}\n"
            if branch_result.stderr:
                error_msg += f"分支推送失败: {branch_result.stderr}"
            raise Exception(error_msg)

        # 返回原始目录
        os.chdir("..")

        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

        return True

    except subprocess.CalledProcessError as e:
        error_lines = e.stderr.splitlines() if e.stderr else []
        error_msg = "\n".join(
            [line for line in error_lines if "error:" in line or "fatal:" in line]
        )
        if not error_msg:
            error_msg = f"命令执行失败: {e.cmd}\n返回码: {e.returncode}"
        raise Exception(error_msg)
    except Exception:
        raise
    finally:
        # 确保清理临时目录
        try:
            if "temp_dir" in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


def sync_repository(github_url, repo_name, auth_url):
    """同步代码到阿里云仓库（主函数，选择最佳方式）"""
    try:
        # 先尝试原方法
        print("🔄 尝试标准同步方法...")
        return sync_repository_standard(github_url, repo_name, auth_url)
    except Exception as e:
        print(f"ℹ️ 标准方法失败: {str(e)}")
        print("🔄 切换到导入代码库方法...")
        return sync_repository_import_method(github_url, repo_name, auth_url)


def sync_repository_standard(github_url, repo_name, auth_url):
    """标准同步方法"""
    try:
        # 克隆 GitHub 仓库
        print(f"🔄 克隆 GitHub 仓库: {github_url}")
        subprocess.run(
            ["git", "clone", "--depth=1", github_url, repo_name],
            check=True,
            capture_output=True,
            text=True,
        )

        # 进入仓库目录
        os.chdir(repo_name)

        # 添加阿里云远程
        print("🔄 添加阿里云远程仓库...")
        subprocess.run(
            ["git", "remote", "add", "aliup", auth_url],
            check=True,
            capture_output=True,
            text=True,
        )

        # 获取当前分支名
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        current_branch = branch_result.stdout.strip()

        # 尝试推送（先尝试非强制推送）
        print("🔄 推送代码到阿里云...")
        push_result = subprocess.run(
            ["git", "push", "aliup", f"{current_branch}:main", "--force-with-lease"],
            capture_output=True,
            text=True,
        )

        # 如果非强制推送失败，尝试强制推送
        if push_result.returncode != 0:
            print("ℹ️ 非强制推送失败，尝试强制推送...")
            subprocess.run(
                ["git", "push", "aliup", f"{current_branch}:main", "--force"],
                check=True,
                capture_output=True,
                text=True,
            )

        # 返回上级目录
        os.chdir("..")
        return True

    except subprocess.CalledProcessError as e:
        error_lines = e.stderr.splitlines() if e.stderr else []
        error_msg = "\n".join(
            [line for line in error_lines if "error:" in line or "fatal:" in line]
        )
        if not error_msg:
            error_msg = f"命令执行失败: {e.cmd}\n返回码: {e.returncode}"
        raise Exception(error_msg)
    except Exception:
        raise


def main():
    """主函数"""
    # 设置命令行参数解析器
    parser = argparse.ArgumentParser(description="同步GitHub仓库到阿里云Codeup")

    # 添加所有必要的参数
    parser.add_argument(
        "--changed-plugins", type=str, required=True, help="JSON格式的变更插件列表"
    )
    parser.add_argument("--org-id", type=str, required=True, help="阿里云组织ID")
    parser.add_argument("--group-path", type=str, required=True, help="阿里云组路径")
    parser.add_argument("--aliyun-account", type=str, required=True, help="阿里云账号")
    parser.add_argument("--aliyun-password", type=str, required=True, help="阿里云密码")
    parser.add_argument(
        "--access-key-id", type=str, required=True, help="阿里云AccessKey ID"
    )
    parser.add_argument(
        "--access-key-secret", type=str, required=True, help="阿里云AccessKey Secret"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("阿里云代码同步任务开始")
    print("=" * 50)

    try:
        # 解析变更插件数据
        try:
            changed_plugins = json.loads(args.changed_plugins)
        except json.JSONDecodeError as e:
            raise ValueError(f"解析变更插件列表失败: {str(e)}")

        # 如果没有变更，直接退出
        if not changed_plugins:
            print("ℹ️ 没有检测到插件变更，无需同步")
            return

        print(f"检测到 {len(changed_plugins)} 个变更插件")

        # 初始化阿里云客户端
        aliyun_client = get_client(
            access_key_id=args.access_key_id, access_key_secret=args.access_key_secret
        )
        print("✅ 阿里云客户端初始化成功")

        results = []

        for plugin in changed_plugins:
            github_url = plugin["github_url"]
            repo_name = plugin["repo_name"]

            # 创建阿里云认证 URL
            auth_url = f"https://{args.aliyun_account}:{args.aliyun_password}@codeup.aliyun.com/{args.org_id}/{args.group_path}/{repo_name}.git"
            display_url = f"https://codeup.aliyun.com/{args.org_id}/{args.group_path}/{repo_name}.git"

            print("\n" + "-" * 50)
            print(f"🔄 处理插件: {plugin.get('name', repo_name)}")
            print(f"GitHub 地址: {github_url}")
            print(f"阿里云地址: {display_url}")
            print("-" * 50)

            try:
                # 1. 创建阿里云仓库
                print("🔄 检查/创建阿里云仓库...")
                if not create_repository(
                    client=aliyun_client, org_id=args.org_id, repo_name=repo_name
                ):
                    raise Exception(f"仓库创建失败: {repo_name}")

                # 2. 同步代码（会自动选择最佳方法）
                sync_repository(github_url, repo_name, auth_url)

                results.append(
                    {
                        "name": plugin.get("name", ""),
                        "github_url": github_url,
                        "aliurl": display_url,
                        "status": "success",
                    }
                )
                print(f"✅ 成功同步: {repo_name} → 阿里云 Codeup")

            except Exception as e:
                print(f"❌ {repo_name} 同步失败: {str(e)}")
                results.append(
                    {
                        "name": plugin.get("name", ""),
                        "github_url": github_url,
                        "status": "failed",
                        "error": str(e),
                    }
                )

                # 清理可能残留的目录
                try:
                    if os.path.exists(repo_name):
                        shutil.rmtree(repo_name, ignore_errors=True)
                except Exception:
                    pass

        # 输出处理结果
        print("\n" + "=" * 50)
        print("同步任务完成")
        print("=" * 50)
        for result in results:
            status = "✅ 成功" if result["status"] == "success" else "❌ 失败"
            print(f"{status}: {result['name']} ({result['github_url']})")

        # 将结果写入文件
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("✅ 结果已保存到 results.json")

        # 如果有失败的任务，返回非零退出码
        if any(r["status"] == "failed" for r in results):
            print("❌ 部分插件同步失败")
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print("\n" + "=" * 50)
        print("❌ 发生严重错误")
        print("=" * 50)
        print(f"错误信息: {str(e)}")
        print(f"错误类型: {type(e).__name__}")

        # 写入错误结果
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump([{"status": "error", "error": str(e)}], f, ensure_ascii=False)

        sys.exit(1)


if __name__ == "__main__":
    main()
