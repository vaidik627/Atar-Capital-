document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://localhost:8000/api';

    // --- State Management ---
    const state = {
        isAuthenticated: false,
        user: null,
        currentView: 'dashboard',
        currentDealId: null
    };

    // --- DOM Elements ---
    const authContainer = document.getElementById('auth-container');
    const appContainer = document.getElementById('app-container');
    const authForm = document.getElementById('auth-form');
    const authBtn = document.getElementById('auth-btn');
    const toggleAuth = document.getElementById('toggle-auth');
    const toggleText = document.getElementById('toggle-text');
    const authSubtitle = document.getElementById('auth-subtitle');
    const emailInput = document.getElementById('email');
    const logoutBtn = document.getElementById('logout-btn');
    const displayName = document.getElementById('display-name');
    const userInitials = document.getElementById('user-initials');
    const navItems = document.querySelectorAll('.nav-item');
    const pageTitle = document.getElementById('page-title');
    const contentArea = document.getElementById('content-area');

    // --- Authentication Logic ---

    // Toggle between Login and Signup (Visual only for now)
    let isLogin = true;
    toggleAuth.addEventListener('click', (e) => {
        e.preventDefault();
        isLogin = !isLogin;
        if (isLogin) {
            authSubtitle.textContent = 'Welcome back! Please login to your account.';
            authBtn.textContent = 'Sign In';
            toggleText.innerHTML = 'Don\'t have an account? <a href="#" id="toggle-auth">Sign Up</a>';
        } else {
            authSubtitle.textContent = 'Create an account to get started.';
            authBtn.textContent = 'Create Account';
            toggleText.innerHTML = 'Already have an account? <a href="#" id="toggle-auth">Sign In</a>';
        }
        // Re-attach event listener since innerHTML replaced the element
        document.getElementById('toggle-auth').addEventListener('click', arguments.callee);
    });

    // Handle Auth Form Submit
    authForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = emailInput.value;
        
        // Mock Login
        state.isAuthenticated = true;
        state.user = {
            email: email,
            name: email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1) // Capitalize part before @
        };

        // Update UI
        updateUserProfile();
        showApp();
    });

    // Handle Logout
    logoutBtn.addEventListener('click', () => {
        state.isAuthenticated = false;
        state.user = null;
        showAuth();
        emailInput.value = '';
    });

    function updateUserProfile() {
        if (state.user) {
            displayName.textContent = state.user.name;
            userInitials.textContent = state.user.name.substring(0, 2).toUpperCase();
        }
    }

    function showApp() {
        authContainer.classList.add('hidden');
        appContainer.classList.remove('hidden');
        renderView('dashboard'); // Default view
    }

    function showAuth() {
        appContainer.classList.add('hidden');
        authContainer.classList.remove('hidden');
    }

    // --- Navigation Logic ---

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Update Active State
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Get View Name
            const viewName = item.getAttribute('data-view');
            renderView(viewName);
        });
    });

    // --- View Rendering (Mock Structure) ---

    function renderView(viewName) {
        state.currentView = viewName;
        
        // Update Header
        const titles = {
            'dashboard': 'Dashboard',
            'upload': 'Upload Document',
            'active-deals': 'Active Deals',
            'analysis': 'Deal Analysis',
            'settings': 'Settings'
        };
        pageTitle.textContent = titles[viewName] || 'Dashboard';

        // Render Content
        let html = '';
        switch(viewName) {
            case 'dashboard':
                html = `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
                        <div class="card">
                            <h3>Active Deals</h3>
                            <div style="height: 100px; display: flex; align-items: center; justify-content: center; color: #94a3b8;">
                                No active deals
                            </div>
                        </div>
                        <div class="card">
                            <h3>Recent Activity</h3>
                            <div style="height: 100px; display: flex; align-items: center; justify-content: center; color: #94a3b8;">
                                No recent activity
                            </div>
                        </div>
                        <div class="card">
                            <h3>System Status</h3>
                            <div style="height: 100px; display: flex; align-items: center; justify-content: center; color: #10b981;">
                                <i class="fas fa-check-circle" style="margin-right: 8px;"></i> All systems operational
                            </div>
                        </div>
                    </div>
                `;
                break;
            case 'upload':
                html = `
                    <div class="card" style="max-width: 800px; margin: 0 auto; padding: 2rem;">
                        <h3 style="margin-bottom: 1.5rem; text-align: center;">Upload New Deal</h3>
                        
                        <div class="form-group" style="margin-bottom: 1.5rem;">
                            <label style="display: block; margin-bottom: 0.5rem; font-weight: 500; color: var(--text-secondary);">Deal Name</label>
                            <input type="text" id="deal-name-input" placeholder="e.g. Project Manta Ray" class="input-wrapper" style="width: 100%; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 6px;">
                        </div>

                        <div class="form-group" style="margin-bottom: 2rem;">
                            <label style="display: block; margin-bottom: 0.5rem; font-weight: 500; color: var(--text-secondary);">Deal Value</label>
                            <input type="text" id="deal-value-input" placeholder="e.g. $50M" class="input-wrapper" style="width: 100%; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 6px;">
                        </div>

                        <div id="drop-zone" style="border: 2px dashed var(--border-color); border-radius: 8px; padding: 3rem; text-align: center; cursor: pointer; transition: all 0.2s; background: #f8fafc;">
                            <i class="fas fa-cloud-upload-alt" style="font-size: 3rem; color: #cbd5e1; margin-bottom: 1rem;"></i>
                            <p style="color: #64748b; margin-bottom: 0.5rem;">Drag and drop PDF files here or click to browse</p>
                            <span class="btn-secondary" style="pointer-events: none;">Select File</span>
                            <input type="file" id="file-input" accept=".pdf" style="display: none;">
                        </div>
                        
                        <div id="file-preview" style="margin-top: 1.5rem; display: none; align-items: center; justify-content: space-between; padding: 1rem; background: #fff; border: 1px solid var(--border-color); border-radius: 6px;">
                            <div style="display: flex; align-items: center; gap: 1rem;">
                                <i class="fas fa-file-pdf" style="color: #ef4444; font-size: 1.5rem;"></i>
                                <span id="file-name" style="font-weight: 500;">filename.pdf</span>
                            </div>
                            <button id="remove-file" style="background: none; border: none; color: #94a3b8; cursor: pointer;"><i class="fas fa-times"></i></button>
                        </div>

                        <div id="upload-status" style="margin-top: 1.5rem; display: none;">
                            <div class="spinner" style="margin-bottom: 0.5rem;"><i class="fas fa-spinner fa-spin"></i> Processing...</div>
                            <div class="status-text">Uploading and extracting data...</div>
                        </div>

                        <button id="upload-submit-btn" class="btn-primary" style="width: 100%; margin-top: 2rem;" disabled>Upload & Analyze</button>
                    </div>
                `;
                break;
            case 'active-deals':
                html = `
                    <div class="card">
                        <div class="section-header">
                            <h3>Active Deals</h3>
                            <button class="btn-secondary" onclick="document.querySelector('[data-view=\\'upload\\']').click()"><i class="fas fa-plus"></i> New Deal</button>
                        </div>
                        <div id="deals-list-container">
                             <div style="padding: 3rem; text-align: center; color: #94a3b8;">
                                <i class="fas fa-spinner fa-spin"></i> Loading deals...
                            </div>
                        </div>
                    </div>
                `;
                break;
            case 'analysis':
                html = `
                    <div style="margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between;">
                         <div style="display: flex; align-items: center; gap: 1rem;">
                            <label style="font-weight: 500; color: var(--text-secondary);">Select Deal:</label>
                            <select id="deal-selector" style="padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 6px; min-width: 250px;">
                                <option value="">-- Select a Deal --</option>
                            </select>
                         </div>
                         <div id="deals-count-badge" class="badge" style="background: var(--primary-color); color: white; padding: 0.5rem 1rem;">
                            0 Deals Uploaded
                         </div>
                    </div>

                    <div id="analysis-content">
                        <div class="card">
                            <div class="empty-state" style="padding: 4rem;">
                                <div style="text-align: center;">
                                    ${state.currentDealId ? 
                                        `<i class="fas fa-spinner fa-spin" style="font-size: 3rem; color: var(--secondary-color); margin-bottom: 1rem;"></i>
                                         <p>Loading analysis data...</p>` : 
                                        `<i class="fas fa-chart-line" style="font-size: 3rem; color: #cbd5e1; margin-bottom: 1rem;"></i>
                                         <p>Select a deal to view detailed analysis</p>`
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                break;
            case 'settings':
                html = `
                    <div class="card" style="max-width: 600px;">
                        <h3>Account Settings</h3>
                        <div style="margin-top: 2rem;">
                            <div class="form-group">
                                <label>Display Name</label>
                                <input type="text" class="input-wrapper" style="width: 100%; padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 4px;" value="${state.user ? state.user.name : ''}" disabled>
                            </div>
                            <div class="form-group">
                                <label>Email Address</label>
                                <input type="email" class="input-wrapper" style="width: 100%; padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 4px;" value="${state.user ? state.user.email : ''}" disabled>
                            </div>
                        </div>
                    </div>
                `;
                break;
            default:
                html = '<div class="empty-state"><p>View not found</p></div>';
        }

        contentArea.innerHTML = html;

        function renderProfitRow(label, data, isRevenue = false, symbol = '') {
            let content = '';
            
            // Helper to ensure symbol is displayed
            const formatValue = (val) => {
                if (!val || val === '-') return '-';
                // Avoid double symbol if already present
                if (val.toString().includes(symbol)) return val;
                return `${symbol}${val}`;
            };

            const appendMillions = (val) => {
                 if (!val || val.toString().toLowerCase().includes('million')) return val;
                 return `${val} Million`;
            };
            
            if (isRevenue && data) {
                // Handle single revenue object
                const val = formatValue(data.value);
                const unit = data.unit || '';
                const per = data.period || '';
                content = `
                    <div style="text-align: right;">
                        <div style="font-weight: 600;">${appendMillions(val)} ${unit}</div>
                        ${per ? `<div style="font-size: 0.75rem; color: #94a3b8;">${per}</div>` : ''}
                    </div>
                `;
            } else if (Array.isArray(data) && data.length > 0) {
                // Handle array of profit metrics
                content = `
                    <div style="text-align: right; display: flex; flex-direction: column; gap: 4px;">
                        ${data.map(item => `
                            <div>
                                <span style="font-weight: 600;">${formatValue(item.value)} ${item.unit || ''}</span>
                                <span style="font-size: 0.75rem; color: #94a3b8; margin-left: 6px;">(${item.period || 'N/A'})</span>
                            </div>
                        `).join('')}
                    </div>
                `;
            } else {
                return ''; // Don't render empty rows
            }

            return `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; padding: 0.5rem 0; border-bottom: 1px solid #f8fafc; font-size: 0.9rem;">
                    <span style="color: var(--text-secondary); margin-top: 2px;">${label}</span>
                    ${content}
                </div>
            `;
        }

        function renderMarginCard(label, data, color) {
            if (!Array.isArray(data) || data.length === 0) return '';
            
            const latest = data[0];
            const value = latest.value;
            if (!value) return '';

            return `
                <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid ${color};">
                    <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem;">${label}</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary);">
                        ${value}%
                    </div>
                    <div style="font-size: 0.75rem; color: #94a3b8;">${latest.period || 'Latest'}</div>
                </div>
            `;
        }

        // Attach event listeners for specific views
        if (viewName === 'analysis' && state.currentDealId) {
            loadAnalysisData(state.currentDealId);
        }



        /* Cash Flow Table Rendering Removed */

        /* Financial Matrix Rendering Removed */

        function renderAnalysisDashboard(data) {
            const container = document.getElementById('analysis-content');
            
            // Helper to format numbers safely
            const fmt = (val) => val !== undefined && val !== null ? val : 'N/A';
            
            // Helper to get currency symbol
            const getCurrencySymbol = (code) => {
                if (!code) return '';
                const map = {
                    'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CNY': '¥', 'INR': '₹',
                    'CAD': 'C$', 'AUD': 'A$', 'CHF': 'Fr'
                };
                return map[code.toUpperCase()] || code;
            };

            const currencyCode = data.header.currency || 'USD';
            const currencySymbol = getCurrencySymbol(currencyCode);
            
            let html = `
                <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                    
                    <!-- Header Section -->
                    <div class="card" style="border-left: 4px solid var(--secondary-color);">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <h2 style="margin: 0; color: var(--primary-color);">${fmt(data.header.companyName)}</h2>
                                <p style="color: var(--text-secondary); margin-top: 0.5rem;">
                                    Currency: <span style="font-weight: 600;">${fmt(currencyCode)} (${currencySymbol})</span>
                                </p>
                            </div>
                            <div style="text-align: right; display: flex; flex-direction: column; gap: 0.5rem;">
                                <div>
                                    <div style="font-size: 0.875rem; color: var(--text-secondary);">Proposed Deal Value</div>
                                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary-color);">
                                        ${currencySymbol} ${fmt(data.header.dealValue.display).toString().replace(currencySymbol, '').trim()}
                                    </div>
                                </div>
                                <div>
                                    <div style="font-size: 0.875rem; color: var(--text-secondary);">Market Size</div>
                                    <div style="font-size: 1.25rem; font-weight: 600; color: var(--success-color);">
                                        ${fmt(data.header.marketSize ? data.header.marketSize.display : 'N/A')}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div style="margin-top: 1.5rem; background: #f8fafc; padding: 1rem; border-radius: 8px;">
                            <h4 style="margin-top: 0; font-size: 0.9rem; color: var(--text-secondary);">EXECUTIVE SUMMARY</h4>
                            <p style="margin-bottom: 0; line-height: 1.6;">${fmt(data.summary.text)}</p>
                        </div>
                    </div>

                    <!-- AI Suggestion -->
                    <div class="card" style="background: linear-gradient(to right, #f0f9ff, #e0f2fe); border: 1px solid #bae6fd;">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                            <div style="background: var(--secondary-color); color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div>
                                <h3 style="margin: 0;">AI Recommendation</h3>
                                <span style="font-size: 0.875rem; color: var(--text-secondary);">Confidence: ${fmt(data.aiSuggestion.confidence)}%</span>
                            </div>
                        </div>
                        <div style="font-size: 1.25rem; font-weight: 600; color: var(--primary-color); margin-bottom: 0.5rem;">
                            ${fmt(data.aiSuggestion.recommendation)}
                        </div>
                        <p style="margin: 0;">${fmt(data.aiSuggestion.rationale)}</p>
                    </div>

                    <!-- Financials Grid -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem;">
                        
                        <!-- Revenue Analysis -->
                        <div class="card">
                            <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                                <i class="fas fa-money-bill-wave" style="color: var(--success-color); margin-right: 0.5rem;"></i> Revenue Analysis
                            </h3>
                            
                            <div style="display: flex; justify-content: space-between; margin-bottom: 1.5rem;">
                                <div>
                                    <div style="font-size: 0.875rem; color: var(--text-secondary);">Present Revenue</div>
                                    <div style="font-size: 1.25rem; font-weight: 600;">${currencySymbol}${fmt(data.revenue.present.value).toString().replace(currencySymbol, '')} Million (${fmt(data.revenue.present.period)})</div>
                                </div>
                            </div>

                            <table style="width: 100%; font-size: 0.9rem;">
                                <thead>
                                    <tr style="text-align: left; color: var(--text-secondary);">
                                        <th style="padding-bottom: 0.5rem;">Period</th>
                                        <th style="padding-bottom: 0.5rem;">Revenue (${currencySymbol})</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${(data.revenue.history || []).map(h => `
                                        <tr>
                                            <td style="padding: 0.5rem 0; border-top: 1px solid #f1f5f9;">${h.period}</td>
                                            <td style="padding: 0.5rem 0; border-top: 1px solid #f1f5f9; font-weight: 500;">
                                                ${currencySymbol}${h.value.toString().replace(currencySymbol, '')} ${h.unit || ''}
                                            </td>
                                        </tr>
                                    `).join('')}
                                    ${(data.revenue.future || []).map(f => `
                                        <tr style="color: var(--text-secondary);">
                                            <td style="padding: 0.5rem 0; border-top: 1px solid #f1f5f9;">${f.period} (E)</td>
                                            <td style="padding: 0.5rem 0; border-top: 1px solid #f1f5f9;">
                                                ${currencySymbol}${f.value.toString().replace(currencySymbol, '')} ${f.unit || ''}
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>

                        <!-- Profitability -->
                        <div class="card">
                            <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                                <i class="fas fa-chart-pie" style="color: var(--warning-color); margin-right: 0.5rem;"></i> Profitability
                            </h3>
                            
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
                                <!-- Profitability & Margins -->
                                <div>
                                    <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em;">Core Profitability</h4>
                                    
                                    <div style="margin-bottom: 1rem;">
                                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; padding-bottom: 0.25rem; border-bottom: 1px solid #e2e8f0; margin-bottom: 0.5rem;">
                                        <span>Metric</span>
                                        <span>Values (Period)</span>
                                    </div>
                                        
                                        ${renderProfitRow(`Revenue (${currencySymbol})`, data.revenue?.present, true, currencySymbol)}
                                        ${renderProfitRow(`Gross Profit (${currencySymbol})`, data.profitMetrics?.gross_profit, false, currencySymbol)}
                                        ${renderProfitRow(`EBITDA (${currencySymbol})`, data.profitMetrics?.ebitda, false, currencySymbol)}
                                        ${renderProfitRow(`Op. Income (${currencySymbol})`, data.profitMetrics?.operating_income, false, currencySymbol)}
                                        ${renderProfitRow(`Net Income (${currencySymbol})`, data.profitMetrics?.net_income, false, currencySymbol)}
                                        ${renderProfitRow(`Op. Cash Flow (${currencySymbol})`, data.profitMetrics?.operating_cash_flow, false, currencySymbol)}
                                    </div>
                                </div>

                                <!-- Key Margins -->
                                <div>
                                    <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em;">Key Margins & Ratios</h4>
                                    
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                        ${renderMarginCard('Gross Margin', data.profitMetrics?.gross_margin_percent, '#10b981')}
                                        ${renderMarginCard('EBITDA Margin', data.profitMetrics?.ebitda_margin_percent, '#f59e0b')}
                                        ${renderMarginCard('Op. Margin', data.profitMetrics?.operating_margin_percent, '#3b82f6')}
                                        ${renderMarginCard('Net Margin', data.profitMetrics?.net_margin_percent, '#6366f1')}
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>

                    <!-- Risks & Market -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem;">

                        <!-- Tale of the Tape -->
                        <div class="card">
                            <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                                <i class="fas fa-tape" style="color: var(--primary-color); margin-right: 0.5rem;"></i> Tale of the Tape
                            </h3>
                            
                            <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid var(--primary-color);">
                                <!-- Adjusted EBITDA -->
                                <div style="font-size: 0.9rem; font-weight: 600; color: var(--primary-color); margin-bottom: 0.5rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.25rem;">
                                    Adjusted EBITDA (${currencySymbol}M)
                                </div>
                                
                                <div style="margin-top: 0.5rem; margin-bottom: 1.5rem;">
                                    ${(() => {
                                        const adjEbitda = data.profitMetrics?.adjusted_ebitda || [];
                                        
                                        if (Array.isArray(adjEbitda) && adjEbitda.length > 0) {
                                            const rows = adjEbitda.map(item => `
                                                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #e2e8f0; padding: 0.5rem 0;">
                                                    <span style="font-weight: 500; color: var(--text-secondary);">${item.period || 'N/A'}</span>
                                                    <div style="text-align: right;">
                                                        <span style="font-weight: 700; color: var(--text-primary); display: block;">${item.value}</span>
                                                    </div>
                                                </div>
                                            `).join('');
                                            
                                            return `
                                                <div style="display: flex; flex-direction: column;">
                                                    ${rows}
                                                </div>
                                            `;
                                        } else {
                                            return `<div style="font-style: italic; color: #94a3b8;">Not available</div>`;
                                        }
                                    })()}
                                </div>

                                <div style="font-size: 0.9rem; font-weight: 600; color: var(--primary-color); margin-bottom: 0.5rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.25rem;">
                                    CAPEX ($M)
                                </div>
                                
                                <div style="margin-top: 0.5rem;">
                                    ${(() => {
                                        const capex = data.tale_of_the_tape?.capex || {};
                                        const yearWise = capex.year_wise || {};
                                        
                                        // If we have year-wise data
                                        if (yearWise && Object.keys(yearWise).length > 0) {
                                            const rows = Object.entries(yearWise).map(([year, val]) => {
                                                // Handle both string values and object values {value, source}
                                                const displayVal = typeof val === 'object' && val !== null ? (val.value || '-') : val;
                                                let sourceVal = typeof val === 'object' && val !== null ? (val.source || 'not_found') : (capex.source || 'not_found');
                                                
                                                if (sourceVal === 'derived_from_fcf') sourceVal = 'derived from FCF';
                                                if (sourceVal === 'calculated') sourceVal = 'calculated';
                                                
                                                return `
                                                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #e2e8f0; padding: 0.5rem 0;">
                                                    <span style="font-weight: 500; color: var(--text-secondary);">${year}</span>
                                                    <div style="text-align: right;">
                                                        <span style="font-weight: 700; color: var(--text-primary); display: block;">${displayVal}</span>
                                                        <span style="font-size: 0.65rem; color: #94a3b8;">(${sourceVal})</span>
                                                    </div>
                                                </div>
                                            `}).join('');
                                            
                                            return `
                                                <div style="display: flex; flex-direction: column;">
                                                    ${rows}
                                                </div>
                                            `;
                                        } 
                                        // Fallback for backward compatibility or single value
                                        else if (capex.value) {
                                            return `
                                                <div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary);">
                                                    ${fmt(capex.value)}
                                                </div>
                                            `;
                                        }
                                        else {
                                            return `<div style="font-style: italic; color: #94a3b8;">Not available</div>`;
                                        }
                                    })()}
                                </div>

                                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.5rem; margin-bottom: 1.5rem;">
                                    
                                </div>

                                <!-- Change in Working Capital -->
                                <div style="font-size: 0.9rem; font-weight: 600; color: var(--primary-color); margin-bottom: 0.5rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.25rem;">
                                    Change in Working Capital ($M)
                                </div>
                                
                                <div style="margin-top: 0.5rem;">
                                    ${(() => {
                                        const wc = data.tale_of_the_tape?.change_in_working_capital || {};
                                        const yearWise = wc.year_wise || {};
                                        
                                        if (yearWise && Object.keys(yearWise).length > 0) {
                                            const rows = Object.entries(yearWise).map(([year, val]) => {
                                                const displayVal = typeof val === 'object' && val !== null ? (val.value || '-') : val;
                                                let sourceVal = typeof val === 'object' && val !== null ? (val.source || 'not_found') : (wc.source || 'not_found');
                                                if (sourceVal === 'calculated_from_nwc') sourceVal = 'calculated from NWC';
                                                if (sourceVal === 'calculated_from_components') sourceVal = 'calculated from CA-CL';
                                                
                                                return `
                                                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #e2e8f0; padding: 0.5rem 0;">
                                                    <span style="font-weight: 500; color: var(--text-secondary);">${year}</span>
                                                    <div style="text-align: right;">
                                                        <span style="font-weight: 700; color: var(--text-primary); display: block;">${displayVal}</span>
                                                        <span style="font-size: 0.65rem; color: #94a3b8;">(${sourceVal})</span>
                                                    </div>
                                                </div>
                                            `}).join('');
                                            
                                            return `
                                                <div style="display: flex; flex-direction: column;">
                                                    ${rows}
                                                </div>
                                            `;
                                        } else {
                                            return `<div style="font-style: italic; color: #94a3b8;">Not available</div>`;
                                        }
                                    })()}
                                </div>

                                <!-- 1x Cost -->
                                <div style="font-size: 0.9rem; font-weight: 600; color: var(--primary-color); margin-bottom: 0.5rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.25rem; margin-top: 1.5rem;">
                                    1x Cost ($M)
                                    <div style="font-size: 0.65rem; font-weight: 400; color: #64748b; margin-top: 2px;">
                                        (+ Expense / - Gain)
                                    </div>
                                </div>
                                
                                <div style="margin-top: 0.5rem;">
                                    ${(() => {
                                        const oneTime = data.tale_of_the_tape?.one_time_cost || {};
                                        const yearWise = oneTime.year_wise || {};
                                        
                                        if (yearWise && Object.keys(yearWise).length > 0) {
                                            const rows = Object.entries(yearWise).map(([year, val]) => {
                                                const displayVal = typeof val === 'object' && val !== null ? (val.value || '-') : val;
                                                let sourceVal = typeof val === 'object' && val !== null ? (val.source || 'not_found') : (oneTime.source || 'not_found');
                                                if (sourceVal === 'calculated_from_bridge') sourceVal = 'calculated from bridge';
                                                
                                                return `
                                                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #e2e8f0; padding: 0.5rem 0;">
                                                    <span style="font-weight: 500; color: var(--text-secondary);">${year}</span>
                                                    <div style="text-align: right;">
                                                        <span style="font-weight: 700; color: var(--text-primary); display: block;">${displayVal}</span>
                                                        <span style="font-size: 0.65rem; color: #94a3b8;">(${sourceVal})</span>
                                                    </div>
                                                </div>
                                            `}).join('');
                                            
                                            return `
                                                <div style="display: flex; flex-direction: column;">
                                                    ${rows}
                                                </div>
                                            `;
                                        } else {
                                            return `<div style="font-style: italic; color: #94a3b8;">Not available</div>`;
                                        }
                                    })()}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Risk Analysis -->
                        <div class="card">
                            <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                                <i class="fas fa-exclamation-triangle" style="color: var(--danger-color); margin-right: 0.5rem;"></i> Risk Analysis
                            </h3>
                            
                            <div style="display: flex; flex-direction: column; gap: 1rem;">
                                ${data.riskAnalysis.operational.length > 0 ? `
                                    <div>
                                        <span class="badge" style="background: #fee2e2; color: #991b1b; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">OPERATIONAL</span>
                                        <ul style="margin: 0.5rem 0 0 1.25rem; color: var(--text-primary);">
                                            ${data.riskAnalysis.operational.map(r => `<li>${r}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                                
                                ${data.riskAnalysis.financial.length > 0 ? `
                                    <div>
                                        <span class="badge" style="background: #ffedd5; color: #9a3412; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">FINANCIAL</span>
                                        <ul style="margin: 0.5rem 0 0 1.25rem; color: var(--text-primary);">
                                            ${data.riskAnalysis.financial.map(r => `<li>${r}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}

                                ${data.riskAnalysis.market && data.riskAnalysis.market.length > 0 ? `
                                    <div>
                                        <span class="badge" style="background: #e0f2fe; color: #075985; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">MARKET</span>
                                        <ul style="margin: 0.5rem 0 0 1.25rem; color: var(--text-primary);">
                                            ${data.riskAnalysis.market.map(r => `<li>${r}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}

                                ${data.riskAnalysis.regulatory && data.riskAnalysis.regulatory.length > 0 ? `
                                    <div>
                                        <span class="badge" style="background: #f3e8ff; color: #6b21a8; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">REGULATORY</span>
                                        <ul style="margin: 0.5rem 0 0 1.25rem; color: var(--text-primary);">
                                            ${data.riskAnalysis.regulatory.map(r => `<li>${r}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                            </div>
                        </div>

                        <!-- Market Intelligence -->
                    <div class="card">
                            <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                                <i class="fas fa-globe" style="color: var(--secondary-color); margin-right: 0.5rem;"></i> Market Intelligence
                            </h3>
                            
                            <p><strong>Industry Position:</strong> ${fmt(data.marketIntelligence.industryPosition)}</p>
                            <p><strong>Market Share:</strong> ${fmt(data.marketIntelligence.marketSharePercent)}</p>
                            
                            ${data.marketIntelligence.context ? `
                                <div style="margin-top: 1rem; padding: 0.75rem; background: #f8fafc; border-left: 3px solid #cbd5e1; font-size: 0.85rem; color: var(--text-secondary);">
                                    <i class="fas fa-quote-left" style="margin-right: 0.5rem; opacity: 0.5;"></i>
                                    ${data.marketIntelligence.context}
                                </div>
                            ` : ''}

                            <h4 style="font-size: 0.9rem; margin-top: 1.5rem;">Key Competitors</h4>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                ${(data.marketIntelligence.competitors || []).map(c => `
                                    <span style="background: #f1f5f9; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.875rem;">${c}</span>
                                `).join('')}
                                ${(!data.marketIntelligence.competitors || data.marketIntelligence.competitors.length === 0) ? '<span style="color: #94a3b8;">No competitor data</span>' : ''}
                            </div>
                        </div>

                    </div>

                    <!-- Free Cash Flow Section -->
                    <div class="card" style="margin-bottom: 1.5rem;">
                        <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                            <i class="fas fa-money-bill-wave" style="color: var(--success-color); margin-right: 0.5rem;"></i> Free Cash Flow Analysis
                        </h3>
                        
                        <div style="overflow-x: auto;">
                            ${(() => {
                                const fcf = data.free_cash_flow || {};
                                const historical = (fcf && typeof fcf === 'object') ? (fcf.historical || fcf.year_wise || {}) : {};
                                const forecast = (fcf && typeof fcf === 'object') ? (fcf.forecast_next_5_years || {}) : {};
                                
                                const hasHistorical = historical && typeof historical === 'object' && Object.keys(historical).length > 0;
                                const hasForecast = forecast && typeof forecast === 'object' && Object.keys(forecast).length > 0;

                                const reservedForecastKeys = new Set(['base_year', 'growth_rate_used', 'methodology']);
                                const forecastYears = hasForecast
                                    ? Object.keys(forecast).filter(k => !reservedForecastKeys.has(k)).sort()
                                    : [];

                                if (!hasHistorical && !hasForecast) {
                                    return `<div style="font-style: italic; color: #94a3b8; padding: 1rem; text-align: center;">Free Cash Flow data not available</div>`;
                                }

                                const historicalTable = hasHistorical ? (() => {
                                    const sortedYears = Object.keys(historical).sort();
                                    return `
                                        <div style="margin-bottom: 1rem;">
                                            <div style="font-size: 0.9rem; font-weight: 600; color: var(--primary-color); margin-bottom: 0.5rem;">Historical</div>
                                            <table style="width: 100%; border-collapse: collapse; min-width: 600px;">
                                                <thead>
                                                    <tr style="background: #f8fafc; text-align: left;">
                                                        <th style="padding: 0.75rem; border-bottom: 2px solid #e2e8f0; color: var(--text-secondary); font-size: 0.85rem; width: 20%;">Metric</th>
                                                        ${sortedYears.map(year => `
                                                            <th style="padding: 0.75rem; border-bottom: 2px solid #e2e8f0; color: var(--text-primary); font-weight: 600; text-align: right;">${year}</th>
                                                        `).join('')}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr>
                                                        <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: var(--primary-color);">Free Cash Flow</td>
                                                        ${sortedYears.map(year => {
                                                            const item = historical[year];
                                                            const val = typeof item === 'object' && item !== null ? (item.value || '-') : item;
                                                            return `<td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: 700;">${val}</td>`;
                                                        }).join('')}
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; color: var(--text-secondary); font-size: 0.85rem;">Source</td>
                                                        ${sortedYears.map(year => {
                                                            const item = historical[year];
                                                            const source = typeof item === 'object' && item !== null ? (item.source || '-') : 'not_found';
                                                            return `<td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; text-align: right; font-size: 0.8rem; color: #64748b;">${source}</td>`;
                                                        }).join('')}
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 0.75rem; color: var(--text-secondary); font-size: 0.85rem;">Method</td>
                                                        ${sortedYears.map(year => {
                                                            const item = historical[year];
                                                            const method = typeof item === 'object' && item !== null ? (item.method || '-') : '-';
                                                            return `<td style="padding: 0.75rem; text-align: right; font-size: 0.8rem; color: #94a3b8; font-style: italic;">${method}</td>`;
                                                        }).join('')}
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    `;
                                })() : '';

                                const forecastTable = forecastYears.length > 0 ? (() => {
                                    const baseYear = forecast.base_year || '';
                                    const growthRate = forecast.growth_rate_used || '';
                                    const methodology = forecast.methodology || '-';
                                    return `
                                        <div>
                                            <div style="font-size: 0.9rem; font-weight: 600; color: var(--primary-color); margin-bottom: 0.5rem;">Forecast (Next 5 Years)</div>
                                            <div style="display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 0.75rem; color: var(--text-secondary); font-size: 0.85rem;">
                                                <div>Base year: <span style="color: var(--text-primary); font-weight: 600;">${baseYear || '-'}</span></div>
                                                <div>Growth rate: <span style="color: var(--text-primary); font-weight: 600;">${growthRate || '-'}</span></div>
                                                <div>Methodology: <span style="color: var(--text-primary); font-weight: 600;">${methodology || '-'}</span></div>
                                            </div>
                                            <table style="width: 100%; border-collapse: collapse; min-width: 600px;">
                                                <thead>
                                                    <tr style="background: #f8fafc; text-align: left;">
                                                        <th style="padding: 0.75rem; border-bottom: 2px solid #e2e8f0; color: var(--text-secondary); font-size: 0.85rem; width: 20%;">Metric</th>
                                                        ${forecastYears.map(year => `
                                                            <th style="padding: 0.75rem; border-bottom: 2px solid #e2e8f0; color: var(--text-primary); font-weight: 600; text-align: right;">${year}</th>
                                                        `).join('')}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr>
                                                        <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: var(--primary-color);">Projected FCF</td>
                                                        ${forecastYears.map(year => {
                                                            const val = forecast[year];
                                                            return `<td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: 700;">${val || '-'}</td>`;
                                                        }).join('')}
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    `;
                                })() : (hasForecast ? `
                                    <div style="font-style: italic; color: #94a3b8; padding: 0.5rem 0; text-align: center;">Forecast data not available</div>
                                ` : '');

                                return `${historicalTable}${forecastTable}`;
                            })()}
                        </div>
                    </div>

                    <!-- Report Generation Section -->
                    <div class="card" id="report-section">
                        <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                            <i class="fas fa-file-export" style="color: var(--secondary-color); margin-right: 0.5rem;"></i> Export & Reports
                        </h3>
                        
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                            <div>
                                <h4 style="margin-bottom: 0.5rem;">Generate Excel Report</h4>
                                <p style="color: var(--text-secondary); font-size: 0.9rem;">
                                    Download a detailed Excel report containing all financial metrics, cash flow projections, and analysis data.
                                </p>
                            </div>
                            <button id="generate-report-btn" class="btn-primary" style="width: auto; padding: 0.75rem 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
                                <i class="fas fa-file-excel"></i> Generate Excel Report
                            </button>
                        </div>

                        <!-- Report History -->
                        <h4 style="margin-bottom: 1rem; font-size: 0.95rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em;">Download History</h4>
                        <div id="deal-report-history">
                            <div style="text-align: center; color: #94a3b8; padding: 1rem;">Loading history...</div>
                        </div>
                    </div>
                </div>
            `;
            
            container.innerHTML = html;

            // Attach event listener for Generate Report
            const generateBtn = document.getElementById('generate-report-btn');
            if (generateBtn) {
                generateBtn.addEventListener('click', () => handleGenerateReport(state.currentDealId));
            }

            // Load history
            loadDealReportHistory(state.currentDealId);
        }

        async function handleGenerateReport(dealId) {
            const btn = document.getElementById('generate-report-btn');
            const originalContent = btn.innerHTML;
            
            // Loading State
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Excel...';
            
            try {
                const response = await fetch(`${API_URL}/reports/generate-excel/${dealId}`, {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.success) {
                    // Trigger Download
                    window.location.href = `${API_URL}/reports/download/${result.filename}`;
                    
                    // Update History
                    await loadDealReportHistory(dealId);
                    
                } else {
                    alert('Failed to generate report: ' + result.message);
                }
            } catch (error) {
                console.error('Report generation error:', error);
                alert('An error occurred while generating the report.');
            } finally {
                // Reset Button
                btn.disabled = false;
                btn.innerHTML = originalContent;
            }
        }

        async function loadDealReportHistory(dealId) {
            const container = document.getElementById('deal-report-history');
            if (!container) return;
            
            try {
                const response = await fetch(`${API_URL}/reports/history/${dealId}`);
                const result = await response.json();
                
                if (result.success && result.history && result.history.length > 0) {
                    container.innerHTML = `
                        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                            ${result.history.map(report => `
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: #f8fafc; border-radius: 6px; border: 1px solid #e2e8f0;">
                                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                                        <div style="color: #16a34a; font-size: 1.2rem;">
                                            <i class="fas ${report.filename.toLowerCase().endsWith('.csv') ? 'fa-file-csv' : 'fa-file-excel'}"></i>
                                        </div>
                                        <div>
                                            <div style="font-weight: 500; font-size: 0.9rem;">${report.filename}</div>
                                            <div style="font-size: 0.75rem; color: #64748b;">${new Date(report.timestamp * 1000).toLocaleString()}</div>
                                        </div>
                                    </div>
                                    <a href="${API_URL}/reports/download/${report.filename}" class="btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.8rem; text-decoration: none; color: var(--text-primary);">
                                        <i class="fas fa-download"></i> Download
                                    </a>
                                </div>
                            `).join('')}
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div style="text-align: center; padding: 1.5rem; border: 2px dashed #e2e8f0; border-radius: 6px; color: #94a3b8;">
                            <p>No reports generated yet.</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading history:', error);
                container.innerHTML = '<p style="color: #ef4444; font-size: 0.9rem;">Failed to load history.</p>';
            }
        }

        // Attach event listeners for specific views
        if (viewName === 'upload') {
            const dropZone = document.getElementById('drop-zone');
            const fileInput = document.getElementById('file-input');
            const filePreview = document.getElementById('file-preview');
            const fileNameSpan = document.getElementById('file-name');
            const removeFileBtn = document.getElementById('remove-file');
            const uploadBtn = document.getElementById('upload-submit-btn');
            const dealNameInput = document.getElementById('deal-name-input');
            const dealValueInput = document.getElementById('deal-value-input');
            const uploadStatus = document.getElementById('upload-status');
            const statusText = uploadStatus.querySelector('.status-text');

            let selectedFile = null;

            dropZone.addEventListener('click', () => fileInput.click());

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFileSelection(e.target.files[0]);
                }
            });

            // Drag and drop handlers
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.style.background = '#f1f5f9';
                dropZone.style.borderColor = 'var(--primary-color)';
            });

            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.style.background = '#f8fafc';
                dropZone.style.borderColor = 'var(--border-color)';
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.style.background = '#f8fafc';
                dropZone.style.borderColor = 'var(--border-color)';
                
                if (e.dataTransfer.files.length > 0) {
                    handleFileSelection(e.dataTransfer.files[0]);
                }
            });

            function handleFileSelection(file) {
                if (file.type !== 'application/pdf') {
                    alert('Please select a PDF file.');
                    return;
                }
                selectedFile = file;
                fileNameSpan.textContent = file.name;
                dropZone.style.display = 'none';
                filePreview.style.display = 'flex';
                validateForm();
            }

            removeFileBtn.addEventListener('click', () => {
                selectedFile = null;
                fileInput.value = '';
                filePreview.style.display = 'none';
                dropZone.style.display = 'block';
                validateForm();
            });

            [dealNameInput, dealValueInput].forEach(input => {
                input.addEventListener('input', validateForm);
            });

            function validateForm() {
                const isValid = selectedFile && dealNameInput.value.trim() && dealValueInput.value.trim();
                uploadBtn.disabled = !isValid;
                uploadBtn.style.opacity = isValid ? '1' : '0.5';
            }

            uploadBtn.addEventListener('click', async () => {
                if (!selectedFile) return;
                await uploadFile(selectedFile);
            });

            async function uploadFile(file) {
                // Show loading state
                uploadBtn.disabled = true;
                uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                uploadStatus.style.display = 'block';
                statusText.textContent = `Uploading ${file.name} and extracting data...`;

                const formData = new FormData();
                formData.append('document', file);
                formData.append('dealName', dealNameInput.value.trim());
                formData.append('dealValue', dealValueInput.value.trim());

                try {
                    const response = await fetch(`${API_URL}/documents/upload`, {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error(`Upload failed: ${response.statusText}`);
                    }

                    const result = await response.json();
                    
                    if (result.success) {
                        statusText.textContent = 'Upload complete! OCR processing finished.';
                        statusText.style.color = '#10b981';
                        
                        // Store deal ID and redirect to analysis
                        state.currentDealId = result.dealId;
                        
                        setTimeout(() => {
                            alert('Document uploaded and processed successfully! Redirecting to analysis...');
                            document.querySelector('[data-view="analysis"]').click();
                        }, 1000);
                    } else {
                        throw new Error(result.message || 'Unknown error occurred');
                    }

                } catch (error) {
                    console.error('Error:', error);
                    statusText.textContent = `Error: ${error.message}`;
                    statusText.style.color = '#ef4444';
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = 'Retry Upload';
                }
            }
        }

        if (viewName === 'active-deals') {
            loadActiveDeals();
        }

        async function loadActiveDeals() {
            try {
                const response = await fetch(`${API_URL}/deals`);
                const result = await response.json();
                const container = document.getElementById('deals-list-container');

                if (result.success && result.deals && result.deals.length > 0) {
                    container.innerHTML = `
                        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem;">
                            ${result.deals.map(deal => `
                                <div class="card" style="transition: transform 0.2s; cursor: pointer;" onclick="window.loadDealAnalysis('${deal.id}')">
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                                        <div style="width: 40px; height: 40px; background: #e0f2fe; color: var(--primary-color); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold;">
                                            ${deal.name.substring(0, 2).toUpperCase()}
                                        </div>
                                        <span class="badge" style="background: #dcfce7; color: #166534; padding: 0.25rem 0.5rem; border-radius: 99px; font-size: 0.75rem;">${deal.status}</span>
                                    </div>
                                    <h3 style="margin-bottom: 0.5rem; font-size: 1.1rem;">${deal.name}</h3>
                                    <p style="color: var(--text-secondary); margin-bottom: 1rem; font-size: 0.9rem;">
                                        <i class="fas fa-tag" style="margin-right: 0.5rem;"></i> ${deal.value}
                                    </p>
                                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 1rem; font-size: 0.875rem; color: #94a3b8;">
                                        <span><i class="far fa-calendar-alt"></i> ${deal.date}</span>
                                        <span style="color: var(--primary-color); font-weight: 500;">View Analysis &rarr;</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div style="text-align: center; padding: 3rem; color: #94a3b8;">
                            <i class="fas fa-folder-open" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                            <p>No active deals found. Upload a document to create a new deal.</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading deals:', error);
                document.getElementById('deals-list-container').innerHTML = `<p style="color: #ef4444; text-align: center;">Error loading deals.</p>`;
            }
        }

        // Global helper for deal click
        window.loadDealAnalysis = (dealId) => {
             state.currentDealId = dealId;
             document.querySelector('[data-view="analysis"]').click();
        };

        if (viewName === 'analysis') {
             loadDealsForSelector();
             if (state.currentDealId) {
                 loadAnalysisData(state.currentDealId);
             }
        }

        if (viewName === 'reports') {
            loadReports();
            
            // Attach refresh listener
            const refreshBtn = document.getElementById('refresh-reports');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', loadReports);
            }
        }

        async function loadReports() {
            const container = document.getElementById('reports-list-container');
            if (!container) return;
            
            try {
                container.innerHTML = `
                    <div style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                        <i class="fas fa-spinner fa-spin"></i> Loading reports...
                    </div>
                `;
                
                const response = await fetch(`${API_URL}/reports`);
                const result = await response.json();
                
                if (result.success && result.reports && result.reports.length > 0) {
                    container.innerHTML = `
                        <div style="display: flex; flex-direction: column; gap: 1rem;">
                            ${result.reports.map(report => `
                                <div class="card" style="display: flex; justify-content: space-between; align-items: center; padding: 1rem;">
                                    <div style="display: flex; align-items: center; gap: 1rem;">
                                        <div style="width: 40px; height: 40px; background: #e0f2fe; color: var(--primary-color); border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                                            <i class="fas fa-file-excel"></i>
                                        </div>
                                        <div>
                                            <div style="font-weight: 600; color: var(--text-primary);">${report.filename}</div>
                                            <div style="font-size: 0.8rem; color: var(--text-secondary);">
                                                Generated: ${new Date(report.created_at * 1000).toLocaleString()}
                                            </div>
                                        </div>
                                    </div>
                                    <a href="${API_URL}/reports/download/${report.filename}" class="btn-primary" style="padding: 0.5rem 1rem; font-size: 0.875rem; text-decoration: none;">
                                        <i class="fas fa-download" style="margin-right: 0.5rem;"></i> Download
                                    </a>
                                </div>
                            `).join('')}
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div class="empty-state" style="padding: 3rem; text-align: center;">
                            <i class="fas fa-file-excel" style="font-size: 3rem; color: #cbd5e1; margin-bottom: 1rem;"></i>
                            <p style="color: var(--text-secondary);">No reports generated yet</p>
                            <p style="font-size: 0.875rem; color: #94a3b8; margin-top: 0.5rem;">Go to Analysis view to generate a report.</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading reports:', error);
                container.innerHTML = `
                    <div style="text-align: center; padding: 2rem; color: var(--danger-color);">
                        <i class="fas fa-exclamation-circle" style="margin-bottom: 0.5rem;"></i>
                        <p>Failed to load reports. Please try again.</p>
                    </div>
                `;
            }
        }

        async function loadDealsForSelector() {
            try {
                const response = await fetch(`${API_URL}/deals`);
                const result = await response.json();
                const selector = document.getElementById('deal-selector');
                const badge = document.getElementById('deals-count-badge');

                if (result.success && result.deals) {
                    badge.textContent = `${result.deals.length} Deals Uploaded`;
                    
                    selector.innerHTML = '<option value="">-- Select a Deal --</option>' + 
                        result.deals.map(deal => `<option value="${deal.id}" ${state.currentDealId === deal.id ? 'selected' : ''}>${deal.name}</option>`).join('');
                    
                    selector.addEventListener('change', (e) => {
                        const dealId = e.target.value;
                        if (dealId) {
                            state.currentDealId = dealId;
                            loadAnalysisData(dealId);
                        } else {
                            state.currentDealId = null;
                            document.getElementById('analysis-content').innerHTML = `
                                <div class="card"><div class="empty-state" style="padding: 4rem; text-align: center;">
                                    <i class="fas fa-chart-line" style="font-size: 3rem; color: #cbd5e1; margin-bottom: 1rem;"></i>
                                    <p>Select a deal to view detailed analysis</p>
                                </div></div>`;
                        }
                    });
                }
            } catch (e) {
                console.error("Error loading deals for selector", e);
            }
        }

        async function loadAnalysisData(dealId) {
            const container = document.getElementById('analysis-content');
            container.innerHTML = `
                <div class="card">
                    <div class="empty-state" style="padding: 4rem; text-align: center;">
                         <i class="fas fa-spinner fa-spin" style="font-size: 3rem; color: var(--secondary-color); margin-bottom: 1rem;"></i>
                         <p>Loading analysis data...</p>
                    </div>
                </div>
            `;

            try {
                const response = await fetch(`${API_URL}/analysis/${dealId}`);
                const result = await response.json();

                if (result.success && result.data && Object.keys(result.data).length > 0) {
                    renderAnalysisDashboard(result.data);
                } else {
                    container.innerHTML = `
                        <div class="card">
                            <div class="empty-state" style="padding: 4rem; text-align: center;">
                                <i class="fas fa-exclamation-circle" style="font-size: 3rem; color: #ef4444; margin-bottom: 1rem;"></i>
                                <p>Analysis data not found or still processing.</p>
                                <button class="btn-secondary" onclick="loadAnalysisData('${dealId}')" style="margin-top: 1rem;">Retry</button>
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error fetching analysis:', error);
                container.innerHTML = `
                     <div class="card">
                        <p style="color: #ef4444;">Error loading analysis: ${error.message}</p>
                    </div>
                `;
            }
        }
    }
});
