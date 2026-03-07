// Dutch Tax Calculator - Frontend JavaScript

const app = {
    // API endpoints
    API_INCOME_TYPES: '/api/income-types',
    API_ASSET_TYPES: '/api/asset-types',
    API_ALLOCATION_STRATEGIES: '/api/allocation-strategies',
    API_CALCULATE: '/api/calculate',

    // State
    incomeTypes: [],
    assetTypes: [],
    allocationStrategies: [],
    currentMemberCount: 1,

    // Initialize the app
    init() {
        console.log('Initializing Dutch Tax Calculator app...');
        this.cacheElements();
        this.loadTypes();
        this.attachEventListeners();
        this.renderMembers(1);
        console.log('✓ App initialized');
    },

    // Cache DOM elements
    cacheElements() {
        this.form = document.getElementById('taxForm');
        this.memberCount = document.getElementById('memberCount');
        this.membersContainer = document.getElementById('membersContainer');
        this.taxForm = document.getElementById('taxForm');
        this.resultsSection = document.getElementById('resultsSection');
        this.emptyState = document.getElementById('emptyState');
        this.allocationStrategy = document.getElementById('allocationStrategy');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.clearBtn = document.getElementById('clearBtn');
    },

    // Load income and asset types from API
    async loadTypes() {
        try {
            const [incomeRes, assetRes] = await Promise.all([
                fetch(this.API_INCOME_TYPES),
                fetch(this.API_ASSET_TYPES)
            ]);

            if (!incomeRes.ok || !assetRes.ok) {
                throw new Error(`Income types: ${incomeRes.status}, Asset types: ${assetRes.status}`);
            }

            this.incomeTypes = (await incomeRes.json()).types;
            this.assetTypes = (await assetRes.json()).types;
            console.log('✓ Types loaded:', this.incomeTypes.length, 'income types,', this.assetTypes.length, 'asset types');
        } catch (error) {
            console.error('✗ Error loading types:', error);
            alert('Warning: Could not load form options. Some features may not work.');
        }
    },

    // Attach event listeners
    attachEventListeners() {
        this.memberCount.addEventListener('change', (e) => {
            this.renderMembers(parseInt(e.target.value));
        });

        this.taxForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.calculateTaxes();
        });

        this.clearBtn.addEventListener('click', () => {
            this.clearResults();
        });
    },

    // Render member sections
    renderMembers(count) {
        this.currentMemberCount = count;
        this.membersContainer.innerHTML = '';

        for (let i = 1; i <= count; i++) {
            this.membersContainer.appendChild(this.createMemberCard(i));
        }
    },

    // Create member card HTML
    createMemberCard(memberNumber) {
        const card = document.createElement('div');
        card.className = `member-card member-${memberNumber}`;
        card.id = `member-${memberNumber}`;

        card.innerHTML = `
            <div class="member-card-header">
                <span class="member-card-title">👤 Member ${memberNumber}</span>
                ${this.currentMemberCount > 1 ? `<button type="button" class="remove-member-btn" onclick="app.removeMember(${memberNumber})">Remove</button>` : ''}
            </div>

            <!-- Basic Info -->
            <div class="mb-3">
                <label for="fullName-${memberNumber}" class="form-label">Full Name *</label>
                <input type="text" class="form-control" id="fullName-${memberNumber}" 
                       placeholder="e.g., John Smith" required>
            </div>

            <div class="mb-3">
                <label for="bsn-${memberNumber}" class="form-label">BSN (Tax ID)</label>
                <input type="text" class="form-control" id="bsn-${memberNumber}" 
                       placeholder="9 digits" maxlength="9">
            </div>

            <div class="mb-3">
                <label for="residency-${memberNumber}" class="form-label">Residency Status</label>
                <select class="form-select" id="residency-${memberNumber}">
                    <option value="RESIDENT" selected>Resident (tax credit applies)</option>
                    <option value="NON_RESIDENT">Non-resident</option>
                </select>
            </div>

            <!-- Income Sources -->
            <div class="subsection">
                <label class="subsection-label">💰 Income Sources</label>
                <div id="incomes-${memberNumber}" class="income-list"></div>
                <button type="button" class="add-item-btn" onclick="app.addIncome(${memberNumber})">
                    + Add Income Source
                </button>
            </div>

            <!-- Deductions -->
            <div class="subsection">
                <label class="subsection-label">📝 Deductions</label>
                <div id="deductions-${memberNumber}" class="deduction-list"></div>
                <button type="button" class="add-item-btn" onclick="app.addDeduction(${memberNumber})">
                    + Add Deduction
                </button>
            </div>

            <!-- Withheld Tax -->
            <div class="subsection">
                <label for="withheld-${memberNumber}" class="form-label">Withheld Tax (€)</label>
                <input type="number" class="form-control" id="withheld-${memberNumber}" 
                       placeholder="0.00" min="0" step="0.01" value="0">
            </div>

            <!-- Assets -->
            <div class="subsection">
                <label class="subsection-label">🏦 Assets (Box3)</label>
                <div id="assets-${memberNumber}" class="asset-list"></div>
                <button type="button" class="add-item-btn" onclick="app.addAsset(${memberNumber})">
                    + Add Asset
                </button>
            </div>
        `;

        return card;
    },

    // Add income source input
    addIncome(memberNumber) {
        const incomeList = document.getElementById(`incomes-${memberNumber}`);
        const id = `income-${memberNumber}-${Date.now()}`;

        const row = document.createElement('div');
        row.className = 'item-row two-col';
        row.id = id;

        let optionsHtml = this.incomeTypes.map(type => 
            `<option value="${type.id}">${type.label}</option>`
        ).join('');

        row.innerHTML = `
            <select class="form-select" data-type="income-type">
                ${optionsHtml}
            </select>
            <input type="number" class="form-control" placeholder="Amount (€)" min="0" step="0.01" data-type="income-amount" required>
            <button type="button" class="remove-item-btn" onclick="app.removeItem('${id}')">Remove</button>
        `;

        incomeList.appendChild(row);
    },

    // Add deduction input
    addDeduction(memberNumber) {
        const deductionList = document.getElementById(`deductions-${memberNumber}`);
        const id = `deduction-${memberNumber}-${Date.now()}`;

        const row = document.createElement('div');
        row.className = 'item-row two-col';
        row.id = id;

        row.innerHTML = `
            <input type="text" class="form-control" placeholder="Description" data-type="deduction-desc" required>
            <input type="number" class="form-control" placeholder="Amount (€)" min="0" step="0.01" data-type="deduction-amount" required>
            <button type="button" class="remove-item-btn" onclick="app.removeItem('${id}')">Remove</button>
        `;

        deductionList.appendChild(row);
    },

    // Add asset input
    addAsset(memberNumber) {
        const assetList = document.getElementById(`assets-${memberNumber}`);
        const id = `asset-${memberNumber}-${Date.now()}`;

        const row = document.createElement('div');
        row.className = 'item-row two-col';
        row.id = id;

        let optionsHtml = this.assetTypes.map(type => 
            `<option value="${type.id}">${type.label}</option>`
        ).join('');

        row.innerHTML = `
            <select class="form-select" data-type="asset-type">
                ${optionsHtml}
            </select>
            <input type="number" class="form-control" placeholder="Value (€)" min="0" step="0.01" data-type="asset-value" required>
            <button type="button" class="remove-item-btn" onclick="app.removeItem('${id}')">Remove</button>
        `;

        assetList.appendChild(row);
    },

    // Remove item from list
    removeItem(id) {
        document.getElementById(id).remove();
    },

    // Remove member
    removeMember(memberNumber) {
        document.getElementById(`member-${memberNumber}`).remove();
        this.memberCount.value = this.currentMemberCount - 1;
        this.currentMemberCount--;
    },

    // Collect form data
    collectFormData() {
        const householdId = document.getElementById('householdId').value || 'WEB_001';
        const allocationStrategy = document.getElementById('allocationStrategy').value;
        const members = [];

        for (let i = 1; i <= this.currentMemberCount; i++) {
            const memberCard = document.getElementById(`member-${i}`);
            if (!memberCard) continue;

            const member = {
                full_name: document.getElementById(`fullName-${i}`).value,
                bsn: document.getElementById(`bsn-${i}`).value || '',
                residency_status: document.getElementById(`residency-${i}`).value,
                incomes: [],
                deductions: [],
                withheld_tax: parseFloat(document.getElementById(`withheld-${i}`).value) || 0,
                assets: []
            };

            // Collect incomes
            const incomeRows = memberCard.querySelectorAll('#incomes-' + i + ' .item-row');
            incomeRows.forEach(row => {
                const type = row.querySelector('[data-type="income-type"]').value;
                const amount = row.querySelector('[data-type="income-amount"]').value;
                if (amount) {
                    member.incomes.push({
                        type: type,
                        amount: parseFloat(amount),
                        description: type
                    });
                }
            });

            // Collect deductions
            const deductionRows = memberCard.querySelectorAll('#deductions-' + i + ' .item-row');
            deductionRows.forEach(row => {
                const desc = row.querySelector('[data-type="deduction-desc"]').value;
                const amount = row.querySelector('[data-type="deduction-amount"]').value;
                if (desc && amount) {
                    member.deductions.push({
                        description: desc,
                        amount: parseFloat(amount)
                    });
                }
            });

            // Collect assets
            const assetRows = memberCard.querySelectorAll('#assets-' + i + ' .item-row');
            assetRows.forEach(row => {
                const type = row.querySelector('[data-type="asset-type"]').value;
                const value = row.querySelector('[data-type="asset-value"]').value;
                if (value) {
                    member.assets.push({
                        type: type,
                        value: parseFloat(value),
                        description: type
                    });
                }
            });

            members.push(member);
        }

        return {
            household_id: householdId,
            allocation_strategy: allocationStrategy,
            members: members
        };
    },

    // Calculate taxes
    async calculateTaxes() {
        try {
            this.loadingSpinner.classList.remove('d-none');

            const data = this.collectFormData();

            if (data.members.length === 0) {
                alert('Please add at least one member with income data');
                this.loadingSpinner.classList.add('d-none');
                return;
            }

            console.log('Sending calculation request:', data);

            const response = await fetch(this.API_CALCULATE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            console.log('Response status:', response.status);

            const result = await response.json();

            console.log('Calculation result:', result);

            if (result.error) {
                console.error('API Error:', result.error);
                alert('Error: ' + result.error);
            } else if (result.success) {
                console.log('✓ Calculation successful');
                this.displayResults(result);
            } else {
                console.error('Unexpected response:', result);
                alert('Calculation did not return expected format');
            }
        } catch (error) {
            console.error('✗ Error calculating taxes:', error);
            alert('Error calculating taxes: ' + error.message);
        } finally {
            this.loadingSpinner.classList.add('d-none');
        }
    },

    // Display results
    displayResults(result) {
        console.log('Displaying results:', result);
        
        // Show results, hide empty state
        this.resultsSection.style.display = 'block';
        this.emptyState.style.display = 'none';

        // Update summary cards
        document.getElementById('totalTaxAmount').textContent = this.formatCurrency(result.total_tax);
        document.getElementById('effectiveRateAmount').textContent = result.effective_tax_rate.toFixed(2) + '%';

        // Update Box1
        let box1Html = '';
        for (const [name, details] of Object.entries(result.box1_breakdown)) {
            box1Html += `
                <div class="member-detail">
                    <div class="member-detail-name">${name}</div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Gross Income:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.gross_income)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Deductions:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.deductions)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Taxable Income:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.taxable_income)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Box1 Tax:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.box1_tax)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Withheld Tax:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.withheld_tax)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label"><strong>Net Liability:</strong></span>
                        <span class="member-detail-value"><strong>${this.formatCurrency(details.net_liability)}</strong></span>
                    </div>
                </div>
            `;
        }
        document.getElementById('box1Details').innerHTML = box1Html;
        document.getElementById('box1Total').textContent = this.formatCurrency(result.box1_total);

        // Update Box3
        document.getElementById('totalAssets').textContent = this.formatCurrency(result.total_assets);
        document.getElementById('box3Rate').textContent = result.box3_rate.toFixed(2) + '%';

        let allocationHtml = '';
        for (const [name, amount] of Object.entries(result.box3_allocation)) {
            allocationHtml += `
                <div class="member-detail-row">
                    <span class="member-detail-label">${name}:</span>
                    <span class="member-detail-value">${this.formatCurrency(amount)}</span>
                </div>
            `;
        }
        document.getElementById('box3Allocation').innerHTML = allocationHtml;
        document.getElementById('box3Total').textContent = this.formatCurrency(result.box3_tax);

        // Update final total
        document.getElementById('finalTotalTax').textContent = this.formatCurrency(result.total_tax);
    },

    // Format currency
    formatCurrency(amount) {
        return new Intl.NumberFormat('nl-NL', {
            style: 'currency',
            currency: 'EUR'
        }).format(amount);
    },

    // Clear results
    clearResults() {
        this.resultsSection.style.display = 'none';
        this.emptyState.style.display = 'block';
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
