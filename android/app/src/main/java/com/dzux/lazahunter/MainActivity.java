package com.dzux.lazahunter;

import android.annotation.SuppressLint;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends AppCompatActivity {

    private static final String SERVER_URL = "http://127.0.0.1:8888";
    private WebView webView;
    private SwipeRefreshLayout swipeRefresh;
    private LinearLayout loadingLayout;
    private TextView statusText;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private static boolean serverStarted = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webView);
        swipeRefresh = findViewById(R.id.swipeRefresh);
        loadingLayout = findViewById(R.id.loadingLayout);
        statusText = findViewById(R.id.statusText);

        setupWebView();
        startForegroundServiceIfNeeded();
        startPythonEngineAndServer();
    }

    private void startForegroundServiceIfNeeded() {
        try {
            Intent serviceIntent = new Intent(this, CrawlerForegroundService.class);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                ContextCompat.startForegroundService(this, serviceIntent);
            } else {
                startService(serviceIntent);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void startPythonEngineAndServer() {
        if (serverStarted) {
            checkServerAndLoad();
            return;
        }

        statusText.setText("⚡ Khởi động Engine Python...");

        new Thread(() -> {
            try {
                // 1. Start Chaquopy Python
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(MainActivity.this));
                }
                Python py = Python.getInstance();

                // 2. Configure app directories for SQLite & Web storage
                String filesDir = getFilesDir().getAbsolutePath();
                PyObject os = py.getModule("os");
                os.get("environ").callAttr("__setitem__", "APP_DATA_DIR", filesDir);

                // 3. Launch embedded HTTP Server & background Crawler thread
                mainHandler.post(() -> statusText.setText("🚀 Khởi động Lazada Scanner & Server..."));
                PyObject serverModule = py.getModule("server");
                serverModule.callAttr("start_android_server");

                serverStarted = true;

                // 4. Poll until server is ready
                waitForServerReady();

            } catch (Exception e) {
                e.printStackTrace();
                mainHandler.post(() -> {
                    statusText.setText("Lỗi khởi động: " + e.getMessage());
                    Toast.makeText(MainActivity.this, "Python Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                });
            }
        }).start();
    }

    private void waitForServerReady() {
        int maxAttempts = 30;
        int attempts = 0;
        boolean ready = false;

        while (attempts < maxAttempts && !ready) {
            attempts++;
            try {
                HttpURLConnection conn = (HttpURLConnection) new URL(SERVER_URL + "/api/stats").openConnection();
                conn.setConnectTimeout(1000);
                conn.setReadTimeout(1000);
                int code = conn.getResponseCode();
                if (code == 200) {
                    ready = true;
                }
                conn.disconnect();
            } catch (Exception ignored) {
            }

            if (!ready) {
                try {
                    Thread.sleep(500);
                } catch (InterruptedException ignored) {}
            }
        }

        mainHandler.post(() -> {
            checkServerAndLoad();
        });
    }

    private void checkServerAndLoad() {
        loadingLayout.setVisibility(View.GONE);
        webView.loadUrl(SERVER_URL);
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void setupWebView() {
        WebSettings ws = webView.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setDatabaseEnabled(true);
        ws.setUseWideViewPort(true);
        ws.setLoadWithOverviewMode(true);
        ws.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        ws.setCacheMode(WebSettings.LOAD_DEFAULT);

        swipeRefresh.setOnRefreshListener(() -> {
            webView.reload();
            swipeRefresh.setRefreshing(false);
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();
                return handleUrlNavigation(url);
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return handleUrlNavigation(url);
            }

            private boolean handleUrlNavigation(String url) {
                if (url == null) return false;

                // Handle Lazada Deep Link: open in official Lazada app if installed!
                if (url.contains("lazada.vn") || url.contains("s.lazada.vn") || url.contains("c.lazada.vn")) {
                    try {
                        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                        intent.setPackage("com.lazada.android");
                        startActivity(intent);
                        return true;
                    } catch (Exception e) {
                        // Lazada app not installed, open in default external browser
                        try {
                            Intent browserIntent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                            startActivity(browserIntent);
                            return true;
                        } catch (Exception ignored) {}
                    }
                }

                // If internal URL, let webview load
                if (url.startsWith("http://127.0.0.1") || url.startsWith("http://localhost")) {
                    return false;
                }

                // Any other external links -> open in external browser
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    startActivity(intent);
                    return true;
                } catch (Exception e) {
                    return false;
                }
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                loadingLayout.setVisibility(View.GONE);
                swipeRefresh.setRefreshing(false);
            }
        });
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
