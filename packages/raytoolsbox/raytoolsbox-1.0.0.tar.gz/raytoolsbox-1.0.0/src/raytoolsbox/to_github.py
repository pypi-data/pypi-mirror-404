import requests
# token: str | None = None,  意思是 token 可以是字符串类型，也可以是 None 类型 。默认值是 None 。
def list_github_repos(username: str, token: str | None = None, print_result: bool = True):
    """
    获取 GitHub 仓库列表。
    
    :param username: GitHub 用户名（可以是自己，也可以是别人）
    :param token: 不传则访问别人公开仓库；传入则可访问自己的公开+私有
    :param print_result: 是否打印
    :return: 仓库列表 [{name, size_mb, private}, ...]
    """
    # 选择 API URL
    if token and username:  
        # token 一般只能访问“当前登录用户”
        # 所以如果 username == token中的用户 → /user/repos
        api_url = "https://api.github.com/user/repos"
        use_auth = True
    else:
        # 无 token → 访问公开仓库
        api_url = f"https://api.github.com/users/{username}/repos"
        use_auth = False

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    repos = []
    page = 1

    while True:
        resp = requests.get(api_url, headers=headers, params={"page": page, "per_page": 100})

                # ========== 处理错误 Token ==========
        if resp.status_code == 401:
            print("❌ GitHub Token 无效（Bad credentials）, 请检查：")
            print("   1. Token 是否拼写正确")
            print("   2. Token 是否未过期")
            print("   3. 如果访问别人公开仓库 → 不要传 token")
            return None  # 或者 raise ValueError("无效 Token")

        # ========== 其它错误 ==========
        if resp.status_code != 200:
            raise RuntimeError(
                f"GitHub API 请求失败：{resp.status_code}\n{resp.text}"
            )

        batch = resp.json()
        if not batch:
            break

        for r in batch:
            repos.append({
                "name": r["name"],
                "size_mb": r["size"] / 1024,
                "private": r["private"],
            })

        page += 1

        # 如果是 /user/repos，但 username 不是 token 的用户 → 会只返回公开仓库（合理情况）
    
    # 打印结果
    if print_result:
        for r in repos:
            print(f"{r['name']:25} {r['size_mb']:7.2f} MB  {'private' if r['private'] else 'public'}")

    return repos

if __name__ == "__main__":

    user = "2dust"
    data = list_github_repos(user)
    # print(data)