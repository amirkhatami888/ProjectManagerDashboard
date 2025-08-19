// Frappe Gantt Chart - Enhanced Implementation
// This file provides a robust implementation of Frappe Gantt chart with better error handling

// Global variables
let ganttChart = null;
let ganttData = [];
let currentProjectId = null;
let ganttLibraryLoaded = false;
let ganttCSSLoaded = false;

// Enhanced library loading with multiple fallbacks
function loadGanttLibrary() {
    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (typeof Gantt !== 'undefined' && ganttLibraryLoaded) {
            console.log("✅ Gantt library already loaded");
            resolve();
            return;
        }

        // Check if script tag already exists
        const existingScript = document.querySelector('script[src*="frappe-gantt"]');
        if (existingScript) {
            console.log("✅ Gantt script tag already exists, waiting for load...");
            existingScript.onload = () => {
                ganttLibraryLoaded = true;
                console.log("✅ Gantt library loaded from existing script");
                resolve();
            };
            existingScript.onerror = () => {
                console.error("❌ Existing Gantt script failed to load");
                reject(new Error("Failed to load Gantt library"));
            };
            return;
        }

        // Try multiple CDN sources
        const cdnSources = [
            'https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.umd.js',
            'https://unpkg.com/frappe-gantt@0.6.1/dist/frappe-gantt.umd.js',
            'https://cdnjs.cloudflare.com/ajax/libs/frappe-gantt/0.6.1/frappe-gantt.umd.js'
        ];

        let currentSourceIndex = 0;

        const tryNextSource = () => {
            if (currentSourceIndex >= cdnSources.length) {
                console.error("❌ All CDN sources failed");
                reject(new Error("Failed to load Gantt library from all sources"));
                return;
            }

            const script = document.createElement('script');
            script.src = cdnSources[currentSourceIndex];
            script.type = 'text/javascript';
            
            script.onload = () => {
                ganttLibraryLoaded = true;
                console.log(`✅ Gantt library loaded from: ${cdnSources[currentSourceIndex]}`);
                resolve();
            };
            
            script.onerror = () => {
                console.warn(`⚠️ Failed to load from: ${cdnSources[currentSourceIndex]}`);
                currentSourceIndex++;
                tryNextSource();
            };
            
            document.head.appendChild(script);
        };

        tryNextSource();
    });
}

// Enhanced CSS loading with fallbacks
function loadGanttCSS() {
    return new Promise((resolve) => {
        // Check if already loaded
        if (document.querySelector('link[href*="frappe-gantt"]') && ganttCSSLoaded) {
            console.log("✅ Gantt CSS already loaded");
            resolve();
            return;
        }

        // Check if CSS link already exists
        const existingCSS = document.querySelector('link[href*="frappe-gantt"]');
        if (existingCSS) {
            console.log("✅ Gantt CSS link already exists");
            ganttCSSLoaded = true;
            resolve();
            return;
        }

        // Try multiple CSS sources
        const cssSources = [
            'https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.css',
            'https://unpkg.com/frappe-gantt@0.6.1/dist/frappe-gantt.css',
            'https://cdnjs.cloudflare.com/ajax/libs/frappe-gantt/0.6.1/frappe-gantt.css',
            '/static/css/gantt-persian.css'  // Local fallback
        ];

        let currentSourceIndex = 0;

        const tryNextCSSSource = () => {
            if (currentSourceIndex >= cssSources.length) {
                console.warn("⚠️ All CSS sources failed, but continuing...");
                resolve();
                return;
            }

            const cssLink = document.createElement('link');
            cssLink.rel = 'stylesheet';
            cssLink.href = cssSources[currentSourceIndex];
            
            cssLink.onload = () => {
                ganttCSSLoaded = true;
                console.log(`✅ Gantt CSS loaded from: ${cssSources[currentSourceIndex]}`);
                resolve();
            };
            
            cssLink.onerror = () => {
                console.warn(`⚠️ Failed to load CSS from: ${cssSources[currentSourceIndex]}`);
                currentSourceIndex++;
                tryNextCSSSource();
            };
            
            document.head.appendChild(cssLink);
        };

        tryNextCSSSource();
    });
}

// Show error message with retry option
function showGanttError(message) {
    const container = document.getElementById('gantt-chart-container');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <strong>خطا در ایجاد نمودار گانت</strong><br>
                ${message}<br>
                <div class="mt-3">
                    <button class="btn btn-primary btn-sm me-2" onclick="retryGanttLoad()">تلاش مجدد</button>
                    <button class="btn btn-secondary btn-sm" onclick="location.reload()">بارگذاری مجدد صفحه</button>
                </div>
            </div>
        `;
    }
}

// Show info message
function showGanttInfo(message) {
    const container = document.getElementById('gantt-chart-container');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-info">
                <strong>اطلاعاتی برای نمایش وجود ندارد</strong><br>
                ${message}<br>
                <button class="btn btn-primary btn-sm mt-2" onclick="location.reload()">بارگذاری مجدد</button>
            </div>
        `;
    }
}

// Retry function for global access
window.retryGanttLoad = function() {
    console.log("🔄 Retrying Gantt chart load...");
    if (window.currentGanttData && window.currentProjectId) {
        initializeGanttChart(window.currentGanttData, window.currentProjectId);
    } else {
        location.reload();
    }
};

// Debug function to check Gantt chart status
window.debugGanttStatus = function() {
    const debugInfo = {
        ganttLibraryLoaded: ganttLibraryLoaded,
        ganttCSSLoaded: ganttCSSLoaded,
        ganttAvailable: typeof Gantt !== 'undefined',
        containerExists: !!document.getElementById('gantt-chart-container'),
        currentProjectId: currentProjectId,
        ganttDataLength: ganttData.length,
        windowGanttChartManager: !!window.GanttChartManager,
        scripts: Array.from(document.querySelectorAll('script[src*="frappe-gantt"]')).map(s => s.src),
        cssLinks: Array.from(document.querySelectorAll('link[href*="frappe-gantt"]')).map(l => l.href)
    };
    
    console.log("🔍 Gantt Debug Info:", debugInfo);
    
    const container = document.getElementById('gantt-chart-container');
    if (container) {
        container.innerHTML = `
            <div class="gantt-debug-info">
                <strong>Debug Information:</strong><br>
                Gantt Library Loaded: ${debugInfo.ganttLibraryLoaded}<br>
                Gantt CSS Loaded: ${debugInfo.ganttCSSLoaded}<br>
                Gantt Available: ${debugInfo.ganttAvailable}<br>
                Container Exists: ${debugInfo.containerExists}<br>
                Project ID: ${debugInfo.currentProjectId}<br>
                Data Length: ${debugInfo.ganttDataLength}<br>
                Manager Available: ${debugInfo.windowGanttChartManager}<br>
                Scripts: ${debugInfo.scripts.join(', ')}<br>
                CSS Links: ${debugInfo.cssLinks.join(', ')}
            </div>
        `;
    }
    
    return debugInfo;
};

// Create a simple fallback Gantt chart when the library fails to load
function createFallbackGantt(tasks) {
    if (!tasks || tasks.length === 0) {
        return '<div class="alert alert-info">هیچ زیرپروژه‌ای برای نمایش وجود ندارد</div>';
    }
    
    let html = `
        <div class="fallback-gantt">
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle"></i>
                <strong>نمودار گانت ساده</strong><br>
                کتابخانه اصلی بارگذاری نشد، نمایش نسخه ساده
            </div>
            <div class="fallback-tasks">
    `;
    
    tasks.forEach((task, index) => {
        const startDate = new Date(task.start).toLocaleDateString('fa-IR');
        const endDate = new Date(task.end).toLocaleDateString('fa-IR');
        const progress = task.progress || 0;
        const progressWidth = Math.min(progress, 100);
        
        html += `
            <div class="fallback-task" style="margin-bottom: 15px; padding: 10px; border: 1px solid #dee2e6; border-radius: 6px;">
                <div style="font-weight: bold; margin-bottom: 5px; color: #495057;">${task.name}</div>
                <div style="font-size: 12px; color: #6c757d; margin-bottom: 8px;">
                    <span>شروع: ${startDate}</span> | 
                    <span>پایان: ${endDate}</span> | 
                    <span>پیشرفت: ${progress}%</span>
                </div>
                <div style="background: #e9ecef; border-radius: 10px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #28a745, #20c997); height: 100%; width: ${progressWidth}%; border-radius: 10px;"></div>
                </div>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
    `;
    
    return html;
}

// Process subprojects data
function processSubprojects(subprojects) {
    const today = new Date();
    const processed = [];
    
    console.log("🔄 Processing subprojects:", subprojects);
    
    for (let sp of subprojects) {
        // Ensure all required properties exist
        const processedSp = {
            id: sp.id || `unknown_${Date.now()}`,
            name: sp.name || `زیرپروژه ${sp.id || 'نامشخص'}`,
            start: sp.start || '',
            end: sp.end || '',
            progress: sp.progress || 0,
            relationshipType: sp.relationshipType || 'مستقل',
            relatedId: sp.relatedId || null,
            relationshipDelay: sp.relationshipDelay || 0,
            hasContract: sp.hasContract || false,
            contractAmount: sp.contractAmount || 0,
            imagenaryDuration: sp.imagenaryDuration || 180
        };
        
        // If subproject has existing dates, keep them
        if (processedSp.start && processedSp.end) {
            console.log(`📅 Subproject ${processedSp.name} has dates: ${processedSp.start} to ${processedSp.end}`);
            processed.push(processedSp);
            continue;
        }
        
        // Handle subprojects with contracts but missing dates
        if (processedSp.hasContract) {
            if (!processedSp.start || !processedSp.end) {
                processedSp.start = today.toISOString().split('T')[0];
                processedSp.end = new Date(today.getTime() + processedSp.imagenaryDuration * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
                console.log(`📅 Set contract dates for ${processedSp.name}: ${processedSp.start} to ${processedSp.end}`);
            }
            processed.push(processedSp);
            continue;
        }
        
        // Handle floating subprojects
        if (processedSp.relationshipType === 'شناور' || !processedSp.relatedId) {
            processedSp.start = today.toISOString().split('T')[0];
            processedSp.end = new Date(today.getTime() + processedSp.imagenaryDuration * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            console.log(`📅 Set floating dates for ${processedSp.name}: ${processedSp.start} to ${processedSp.end}`);
            processed.push(processedSp);
            continue;
        }
        
        // For dependent subprojects, we'll calculate dates later
        processed.push(processedSp);
    }
    
    // Calculate dates for dependent subprojects
    let changed = true;
    let iterations = 0;
    
    while (changed && iterations < 10) {
        changed = false;
        iterations++;
        
        for (let sp of processed) {
            if (sp.start && sp.end) continue; // Already has dates
            if (!sp.relatedId || !sp.relationshipType) continue;
            
            const relatedSp = processed.find(rsp => rsp.id === sp.relatedId);
            if (!relatedSp || !relatedSp.start || !relatedSp.end) continue;
            
            const relatedStart = new Date(relatedSp.start);
            const relatedEnd = new Date(relatedSp.end);
            const delay = sp.relationshipDelay || 0;
            
            let newStart, newEnd;
            
            if (sp.relationshipType === 'بعد از') {
                newStart = new Date(relatedEnd.getTime() + delay * 24 * 60 * 60 * 1000);
                newEnd = new Date(newStart.getTime() + sp.imagenaryDuration * 24 * 60 * 60 * 1000);
            } else if (sp.relationshipType === 'قبل از') {
                newEnd = new Date(relatedStart.getTime() - delay * 24 * 60 * 60 * 1000);
                newStart = new Date(newEnd.getTime() - sp.imagenaryDuration * 24 * 60 * 60 * 1000);
            } else if (sp.relationshipType === 'شروع با') {
                newStart = new Date(relatedStart.getTime() + delay * 24 * 60 * 60 * 1000);
                newEnd = new Date(newStart.getTime() + sp.imagenaryDuration * 24 * 60 * 60 * 1000);
            } else if (sp.relationshipType === 'پایان با') {
                newEnd = new Date(relatedEnd.getTime() + delay * 24 * 60 * 60 * 1000);
                newStart = new Date(newEnd.getTime() - sp.imagenaryDuration * 24 * 60 * 60 * 1000);
            } else {
                continue;
            }
            
            sp.start = newStart.toISOString().split('T')[0];
            sp.end = newEnd.toISOString().split('T')[0];
            changed = true;
            console.log(`📅 Calculated dates for ${sp.name}: ${sp.start} to ${sp.end}`);
        }
    }
    
    console.log("✅ Final processed subprojects:", processed);
    return processed;
}

// Convert to Frappe Gantt format
function convertToGanttFormat(subprojects) {
    const tasks = [];
    
    for (let sp of subprojects) {
        if (sp.start && sp.end) {
            const task = {
                id: sp.id.toString(),
                name: sp.name,
                start: sp.start,
                end: sp.end,
                progress: sp.progress || 0,
                dependencies: []
            };
            
            if (sp.relatedId && sp.relationshipType && sp.relationshipType !== 'شناور') {
                task.dependencies.push(sp.relatedId.toString());
            }
            
            tasks.push(task);
        }
    }
    
    console.log("🎯 Converted to Gantt format:", tasks);
    return tasks;
}

// Simple Gantt configuration
const ganttConfig = {
    header_height: 50,
    column_width: 30,
    step: 24,
    view_modes: ['Quarter Day', 'Half Day', 'Day', 'Week', 'Month'],
    view_mode: 'Month',
    date_format: 'YYYY-MM-DD',
    language: 'fa',
    arrow_curve: 6,
    padding: 18,
    bar_height: 40,
    bar_corner_radius: 3,
    bar_progress: true,
    bar_progress_color: '#aaa',
    bar_progress_opacity: 0.3,
    arrow_color: '#ccc',
    row_height: 44,
    today_color: 'rgba(252, 248, 227, 0.5)',
    Tooltip_width: 200,
    // Very simple tooltip to avoid any errors
    Tooltip_template: function (start, end, task) {
        if (!task || !task.name) {
            return '<div>نامشخص</div>';
        }
        
        const startDate = start ? new Date(start).toLocaleDateString('fa-IR') : 'نامشخص';
        const endDate = end ? new Date(end).toLocaleDateString('fa-IR') : 'نامشخص';
        const progress = task.progress || 0;
        
        return `
            <div style="direction: rtl; text-align: right; font-family: Tahoma;">
                <div style="font-weight: bold; margin-bottom: 5px;">${task.name}</div>
                <div style="font-size: 12px;">
                    <div>شروع: ${startDate}</div>
                    <div>پایان: ${endDate}</div>
                    <div>پیشرفت: ${progress}%</div>
                </div>
            </div>
        `;
    }
};

// Initialize Gantt chart
async function initializeGanttChart(subprojects, projectId = null) {
    console.log("🚀 Starting Gantt chart initialization...");
    
    if (projectId) {
        currentProjectId = projectId;
        window.currentProjectId = projectId;
    }
    
    try {
        // Store data for retry functionality
        window.currentGanttData = subprojects;
        
        // Load libraries with timeout
        const loadTimeout = 15000; // 15 seconds timeout
        const loadPromise = Promise.all([loadGanttLibrary(), loadGanttCSS()]);
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error("Library loading timeout")), loadTimeout)
        );
        
        await Promise.race([loadPromise, timeoutPromise]);
        
        // Check if container exists
        const container = document.getElementById('gantt-chart-container');
        if (!container) {
            throw new Error("Gantt chart container not found");
        }
        
        // Check if Frappe Gantt library is loaded
        if (typeof Gantt === 'undefined') {
            console.warn("⚠️ Frappe Gantt library not loaded, trying fallback...");
            
            // Try to create a simple fallback chart
            const container = document.getElementById('gantt-chart-container');
            if (container && ganttTasks.length > 0) {
                container.innerHTML = createFallbackGantt(ganttTasks);
                console.log("✅ Fallback Gantt chart created");
                return null;
            } else {
                throw new Error("Frappe Gantt library not loaded and fallback failed");
            }
        }
        
        console.log("✅ Gantt library loaded successfully");
        
        // Validate subprojects data
        if (!Array.isArray(subprojects)) {
            throw new Error("Subprojects data is not an array");
        }
        
        console.log("📊 Processing subprojects:", subprojects.length);
        
        // Process subprojects
        const processedSubprojects = processSubprojects(subprojects);
        
        // Filter out subprojects without start or end dates
        const validSubprojects = processedSubprojects.filter(sp => sp.start && sp.end);
        
        if (validSubprojects.length === 0) {
            showGanttInfo(`هیچ زیرپروژه معتبری برای نمایش وجود ندارد<br>تعداد زیرپروژه‌های موجود: ${subprojects.length}`);
            return null;
        }
        
        console.log("📊 Valid subprojects count:", validSubprojects.length);
        
        // Convert to Gantt format
        const ganttTasks = convertToGanttFormat(validSubprojects);
        
        if (ganttTasks.length === 0) {
            showGanttInfo("هیچ زیرپروژه معتبری برای نمایش وجود ندارد");
            return null;
        }
        
        console.log("🎯 Creating Gantt chart with tasks:", ganttTasks);
        
        // Clear container
        container.innerHTML = '';
        
        // Initialize the Gantt chart with error handling
        try {
            ganttChart = new Gantt('#gantt-chart-container', ganttTasks, ganttConfig);
            console.log("✅ Gantt chart created successfully:", ganttChart);
        } catch (ganttError) {
            console.error("❌ Error creating Gantt instance:", ganttError);
            throw new Error(`Gantt chart creation failed: ${ganttError.message}`);
        }
        
        // Store reference for refresh functionality
        window.currentGantt = ganttChart;
        window.currentGanttTasks = ganttTasks;
        ganttData = ganttTasks;
        
        // Add click event to navigate to subproject detail
        try {
            ganttChart.bind('click', function(task) {
                const url = window.location.pathname.replace(/\/projects\/\d+\//, `/subprojects/${task.id}/`);
                window.location.href = url;
            });
        } catch (bindError) {
            console.warn("⚠️ Could not bind click event:", bindError);
        }
        
        // Add custom styling
        addCustomStyling();
        
        return ganttChart;
    } catch (error) {
        console.error("❌ Error creating Gantt chart:", error);
        showGanttError(`خطا در ایجاد نمودار گانت: ${error.message}`);
        return null;
    }
}

// Add custom styling
function addCustomStyling() {
    // Check if style already exists
    if (document.querySelector('#gantt-custom-styles')) {
        return;
    }
    
    const style = document.createElement('style');
    style.id = 'gantt-custom-styles';
    style.textContent = `
        .gantt .grid-header {
            direction: rtl;
        }
        
        .gantt .grid-header .grid-row .grid-cell {
            text-align: center;
            font-family: 'Tahoma', 'Arial', sans-serif;
        }
        
        .gantt .grid-body .grid-row .grid-cell {
            direction: rtl;
            text-align: right;
            font-family: 'Tahoma', 'Arial', sans-serif;
        }
        
        .gantt .bar-label {
            direction: rtl;
            text-align: right;
            font-family: 'Tahoma', 'Arial', sans-serif;
        }
        
        .gantt .today-highlight {
            background-color: rgba(255, 193, 7, 0.3);
        }
        
        .gantt .bar-progress {
            background-color: #28a745;
        }
        
        .gantt .bar {
            border-radius: 3px;
        }
        
        .gantt .bar-wrapper:hover .bar {
            opacity: 0.8;
        }
        
        /* Debug info */
        .gantt-debug-info {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-size: 12px;
            color: #6c757d;
        }
    `;
    document.head.appendChild(style);
}

// Refresh functionality
function refreshGanttChart(projectId = null) {
    const targetProjectId = projectId || currentProjectId;
    
    if (!targetProjectId) {
        console.error("❌ No project ID available for refresh");
        return;
    }
    
    console.log("🔄 Refreshing Gantt chart for project:", targetProjectId);
    const refreshBtn = document.getElementById('gantt-refresh-btn');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> در حال بروزرسانی...';
    }
    
    fetch(`/creator_subproject/api/project/${targetProjectId}/gantt-data/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log("✅ Received updated data:", data);
                
                // Recalculate and reinitialize
                initializeGanttChart(data.subprojects, targetProjectId).then(() => {
                    if (refreshBtn) {
                        refreshBtn.innerHTML = '<i class="bi bi-check-circle"></i> بروزرسانی شد';
                        setTimeout(function() {
                            refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> بروزرسانی';
                            refreshBtn.disabled = false;
                        }, 2000);
                    }
                });
            } else {
                console.error('❌ Error fetching updated data:', data.error);
                if (refreshBtn) {
                    refreshBtn.innerHTML = '<i class="bi bi-exclamation-triangle"></i> خطا';
                    setTimeout(function() {
                        refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> بروزرسانی';
                        refreshBtn.disabled = false;
                    }, 3000);
                }
            }
        })
        .catch(error => {
            console.error('❌ Error:', error);
            if (refreshBtn) {
                refreshBtn.innerHTML = '<i class="bi bi-exclamation-triangle"></i> خطا';
                setTimeout(function() {
                    refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> بروزرسانی';
                    refreshBtn.disabled = false;
                }, 3000);
            }
        });
}

// Fullscreen functionality
function toggleFullscreen() {
    const modal = document.getElementById('gantt-modal');
    if (modal) {
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        // Reinitialize chart in fullscreen mode
        setTimeout(() => {
            const fullscreenContainer = document.getElementById('gantt-chart-fullscreen');
            if (fullscreenContainer && ganttData.length > 0) {
                fullscreenContainer.innerHTML = '';
                new Gantt('#gantt-chart-fullscreen', ganttData, {
                    ...ganttConfig,
                    header_height: 60,
                    bar_height: 50,
                    row_height: 50
                });
            }
        }, 500);
    }
}

// Export functions for global use
window.GanttChartManager = {
    initialize: initializeGanttChart,
    refresh: refreshGanttChart,
    showError: showGanttError,
    showInfo: showGanttInfo,
    toggleFullscreen: toggleFullscreen
};
