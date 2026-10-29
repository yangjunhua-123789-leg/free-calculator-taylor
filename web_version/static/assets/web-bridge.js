/* 自由计算器 Web 桥接层
 *
 * 桌面版（pywebview）会注入 window.pywebview.api；Web 版没有该对象，
 * 这里补一个同签名的实现，把调用转发到同源接口 /api/solve。
 * 这样 assets/app.js 完全不用改动，核心逻辑与桌面端保持一致。
 */
(function () {
  "use strict";

  // 桌面端已注入桥接：直接返回，保持原行为
  if (window.pywebview && window.pywebview.api) {
    return;
  }

  var ENDPOINT = "/api/solve";

  async function solve_limit(expression, center, order, direction) {
    var response;
    try {
      response = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          expression: expression,
          center: center,
          max_order: order,
          direction: direction
        })
      });
    } catch (error) {
      throw new Error("无法连接计算服务，请检查网络或稍后重试。");
    }

    var data = null;
    try {
      data = await response.json();
    } catch (error) {
      throw new Error("服务端返回了无法解析的响应（HTTP " + response.status + "）。");
    }

    if (!response.ok && (!data || data.error === undefined)) {
      throw new Error("服务端错误（HTTP " + response.status + "）。");
    }
    return data;
  }

  window.pywebview = { api: { solve_limit: solve_limit } };
  window.dispatchEvent(new Event("pywebviewready"));
})();
