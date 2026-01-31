/**
 * Visual Query Builder for non-technical users.
 * Allows building SQL queries through a visual interface.
 */

// Filter operators organized by column type
const FILTER_OPERATORS = {
    string: [
        { value: '=', label: 'equals' },
        { value: '!=', label: 'does not equal' },
        { value: 'LIKE', label: 'contains' },
        { value: 'NOT LIKE', label: 'does not contain' },
        { value: 'IS NULL', label: 'is empty' },
        { value: 'IS NOT NULL', label: 'is not empty' }
    ],
    number: [
        { value: '=', label: 'equals' },
        { value: '!=', label: 'does not equal' },
        { value: '<', label: 'less than' },
        { value: '<=', label: 'less than or equal' },
        { value: '>', label: 'greater than' },
        { value: '>=', label: 'greater than or equal' },
        { value: 'IS NULL', label: 'is empty' },
        { value: 'IS NOT NULL', label: 'is not empty' }
    ],
    date: [
        { value: '=', label: 'equals' },
        { value: '!=', label: 'does not equal' },
        { value: '<', label: 'before' },
        { value: '<=', label: 'on or before' },
        { value: '>', label: 'after' },
        { value: '>=', label: 'on or after' },
        { value: 'IS NULL', label: 'is empty' },
        { value: 'IS NOT NULL', label: 'is not empty' }
    ]
};

// Map database types to filter type categories
const TYPE_MAPPING = {
    // String types
    'varchar': 'string', 'char': 'string', 'text': 'string', 'longtext': 'string',
    'mediumtext': 'string', 'tinytext': 'string', 'character varying': 'string',
    'nvarchar': 'string', 'nchar': 'string',
    // Number types
    'int': 'number', 'integer': 'number', 'bigint': 'number', 'smallint': 'number',
    'tinyint': 'number', 'decimal': 'number', 'numeric': 'number', 'float': 'number',
    'double': 'number', 'real': 'number', 'double precision': 'number',
    // Date types
    'date': 'date', 'datetime': 'date', 'timestamp': 'date', 'time': 'date',
    'timestamp without time zone': 'date', 'timestamp with time zone': 'date'
};

/**
 * QueryBuilder class for visual query construction.
 */
class QueryBuilder {
    constructor(options = {}) {
        this.tableSelect = options.tableSelect;
        this.columnsContainer = options.columnsContainer;
        this.filtersContainer = options.filtersContainer;
        this.limitSlider = options.limitSlider;
        this.limitValue = options.limitValue;
        this.sqlOutput = options.sqlOutput;
        this.previewBtn = options.previewBtn;
        this.onQueryChange = options.onQueryChange || (() => {});

        this.tables = [];
        this.columns = [];
        this.filters = [];
        this.dbType = 'mysql';
        this.dbParams = {};

        this.init();
    }

    init() {
        if (this.tableSelect) {
            this.tableSelect.addEventListener('change', () => this.onTableChange());
        }
        if (this.limitSlider) {
            this.limitSlider.addEventListener('input', () => this.onLimitChange());
        }
    }

    /**
     * Set database connection parameters.
     */
    setDbParams(params) {
        this.dbParams = params;
        this.dbType = params.db_type || 'mysql';
    }

    /**
     * Build query string for API calls.
     */
    buildQueryString() {
        const params = new URLSearchParams();
        if (this.dbParams.db_type) params.append('db_type', this.dbParams.db_type);
        if (this.dbParams.db_host) params.append('db_host', this.dbParams.db_host);
        if (this.dbParams.db_port) params.append('db_port', this.dbParams.db_port);
        if (this.dbParams.db_user) params.append('db_user', this.dbParams.db_user);
        if (this.dbParams.db_password) params.append('db_password', this.dbParams.db_password);
        if (this.dbParams.db_name) params.append('db_name', this.dbParams.db_name);
        return params.toString();
    }

    /**
     * Load tables from the database.
     */
    async loadTables() {
        try {
            const queryString = this.buildQueryString();
            const response = await fetch(`/api/setup/schema/tables?${queryString}`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message);
            }

            this.tables = data.tables || [];
            this.renderTableSelect();
            return this.tables;
        } catch (error) {
            console.error('Failed to load tables:', error);
            throw error;
        }
    }

    /**
     * Render table dropdown options.
     */
    renderTableSelect() {
        if (!this.tableSelect) return;

        // Clear existing options except placeholder
        this.tableSelect.innerHTML = '<option value="">-- Select a table --</option>';

        this.tables.forEach(table => {
            const option = document.createElement('option');
            option.value = table.name;
            const rowCount = table.row_count !== null ? ` (${table.row_count.toLocaleString()} rows)` : '';
            option.textContent = table.name + rowCount;
            this.tableSelect.appendChild(option);
        });

        // Enable the select
        this.tableSelect.disabled = false;
    }

    /**
     * Handle table selection change.
     */
    async onTableChange() {
        const tableName = this.tableSelect?.value;
        if (!tableName) {
            this.columns = [];
            this.renderColumns();
            return;
        }

        try {
            await this.loadColumns(tableName);
            this.renderColumns();
            this.showColumnSection();
            this.buildAndUpdateSQL();
        } catch (error) {
            console.error('Failed to load columns:', error);
        }
    }

    /**
     * Load columns for a specific table.
     */
    async loadColumns(tableName) {
        try {
            const queryString = this.buildQueryString();
            const response = await fetch(`/api/setup/schema/columns/${encodeURIComponent(tableName)}?${queryString}`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message);
            }

            this.columns = data.columns || [];
            return this.columns;
        } catch (error) {
            console.error('Failed to load columns:', error);
            throw error;
        }
    }

    /**
     * Render column checkboxes.
     */
    renderColumns() {
        if (!this.columnsContainer) return;

        this.columnsContainer.innerHTML = '';

        this.columns.forEach((col, index) => {
            const checkbox = document.createElement('label');
            checkbox.className = 'column-checkbox';
            checkbox.innerHTML = `
                <input type="checkbox" value="${col.name}" checked data-type="${col.type}">
                <span class="column-name">${col.name}</span>
                <span class="column-type">${col.type}</span>
            `;

            const input = checkbox.querySelector('input');
            input.addEventListener('change', () => this.buildAndUpdateSQL());

            this.columnsContainer.appendChild(checkbox);
        });
    }

    /**
     * Show column section after table is selected.
     */
    showColumnSection() {
        const columnsSection = document.getElementById('columns-section');
        const filtersSection = document.getElementById('filters-section');
        const limitSection = document.getElementById('limit-section');

        if (columnsSection) columnsSection.style.display = 'block';
        if (filtersSection) filtersSection.style.display = 'block';
        if (limitSection) limitSection.style.display = 'block';
    }

    /**
     * Get selected columns.
     */
    getSelectedColumns() {
        if (!this.columnsContainer) return ['*'];

        const checkboxes = this.columnsContainer.querySelectorAll('input[type="checkbox"]:checked');
        const selected = Array.from(checkboxes).map(cb => cb.value);

        // If all columns selected, use *
        if (selected.length === this.columns.length) {
            return ['*'];
        }

        return selected.length > 0 ? selected : ['*'];
    }

    /**
     * Select all columns.
     */
    selectAllColumns() {
        if (!this.columnsContainer) return;

        const checkboxes = this.columnsContainer.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = true);
        this.buildAndUpdateSQL();
    }

    /**
     * Deselect all columns.
     */
    deselectAllColumns() {
        if (!this.columnsContainer) return;

        const checkboxes = this.columnsContainer.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
        this.buildAndUpdateSQL();
    }

    /**
     * Handle limit slider change.
     */
    onLimitChange() {
        if (this.limitValue && this.limitSlider) {
            this.limitValue.textContent = parseInt(this.limitSlider.value).toLocaleString();
        }
        this.buildAndUpdateSQL();
    }

    /**
     * Get the current limit value.
     */
    getLimit() {
        return this.limitSlider ? parseInt(this.limitSlider.value) : 1000;
    }

    /**
     * Add a filter row.
     */
    addFilterRow(columnName = '', operator = '=', value = '') {
        if (!this.filtersContainer) return;

        const filterRow = document.createElement('div');
        filterRow.className = 'filter-row';

        // Column select
        const columnSelect = document.createElement('select');
        columnSelect.className = 'form-select filter-column';
        columnSelect.innerHTML = '<option value="">Select column</option>';
        this.columns.forEach(col => {
            const option = document.createElement('option');
            option.value = col.name;
            option.dataset.type = col.type;
            option.textContent = col.name;
            if (col.name === columnName) option.selected = true;
            columnSelect.appendChild(option);
        });

        // Operator select
        const operatorSelect = document.createElement('select');
        operatorSelect.className = 'form-select filter-operator';

        // Value input
        const valueInput = document.createElement('input');
        valueInput.type = 'text';
        valueInput.className = 'form-control filter-value';
        valueInput.placeholder = 'Value';
        valueInput.value = value;

        // Remove button
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-danger btn-sm filter-remove';
        removeBtn.innerHTML = '&times;';
        removeBtn.title = 'Remove filter';

        // Update operators when column changes
        columnSelect.addEventListener('change', () => {
            const selectedOption = columnSelect.options[columnSelect.selectedIndex];
            const colType = selectedOption?.dataset?.type || 'string';
            this.updateOperatorOptions(operatorSelect, colType);
            this.buildAndUpdateSQL();
        });

        operatorSelect.addEventListener('change', () => {
            const selectedOp = operatorSelect.value;
            // Hide value input for IS NULL / IS NOT NULL
            if (selectedOp === 'IS NULL' || selectedOp === 'IS NOT NULL') {
                valueInput.style.display = 'none';
            } else {
                valueInput.style.display = 'block';
            }
            this.buildAndUpdateSQL();
        });

        valueInput.addEventListener('input', () => this.buildAndUpdateSQL());

        removeBtn.addEventListener('click', () => {
            filterRow.remove();
            this.buildAndUpdateSQL();
        });

        // Initialize operators for first column
        const firstColType = this.columns[0]?.type || 'string';
        this.updateOperatorOptions(operatorSelect, firstColType);
        if (operator) {
            operatorSelect.value = operator;
        }

        filterRow.appendChild(columnSelect);
        filterRow.appendChild(operatorSelect);
        filterRow.appendChild(valueInput);
        filterRow.appendChild(removeBtn);

        this.filtersContainer.appendChild(filterRow);
    }

    /**
     * Update operator options based on column type.
     */
    updateOperatorOptions(operatorSelect, colType) {
        const baseType = TYPE_MAPPING[colType.toLowerCase()] || 'string';
        const operators = FILTER_OPERATORS[baseType];

        operatorSelect.innerHTML = '';
        operators.forEach(op => {
            const option = document.createElement('option');
            option.value = op.value;
            option.textContent = op.label;
            operatorSelect.appendChild(option);
        });
    }

    /**
     * Get filter conditions.
     */
    getFilters() {
        if (!this.filtersContainer) return [];

        const filterRows = this.filtersContainer.querySelectorAll('.filter-row');
        const filters = [];

        filterRows.forEach(row => {
            const column = row.querySelector('.filter-column')?.value;
            const operator = row.querySelector('.filter-operator')?.value;
            const value = row.querySelector('.filter-value')?.value;

            if (column && operator) {
                filters.push({ column, operator, value });
            }
        });

        return filters;
    }

    /**
     * Build SQL query from visual selections.
     */
    buildSQL() {
        const table = this.tableSelect?.value;
        if (!table) return '';

        const columns = this.getSelectedColumns();
        const filters = this.getFilters();
        const limit = this.getLimit();

        // Quote column names
        const columnList = columns.map(col => {
            if (col === '*') return '*';
            return this.quoteIdentifier(col);
        }).join(', ');

        let sql = `SELECT ${columnList} FROM ${this.quoteIdentifier(table)}`;

        // Add WHERE clause
        if (filters.length > 0) {
            const conditions = filters.map(f => {
                const quotedCol = this.quoteIdentifier(f.column);

                if (f.operator === 'IS NULL' || f.operator === 'IS NOT NULL') {
                    return `${quotedCol} ${f.operator}`;
                }

                if (f.operator === 'LIKE' || f.operator === 'NOT LIKE') {
                    return `${quotedCol} ${f.operator} '%${this.escapeValue(f.value)}%'`;
                }

                // Detect if value is numeric
                const isNumeric = !isNaN(f.value) && f.value !== '';
                const quotedValue = isNumeric ? f.value : `'${this.escapeValue(f.value)}'`;

                return `${quotedCol} ${f.operator} ${quotedValue}`;
            });

            sql += ` WHERE ${conditions.join(' AND ')}`;
        }

        // Add LIMIT
        sql += ` LIMIT ${limit}`;

        return sql;
    }

    /**
     * Quote identifier based on database type.
     */
    quoteIdentifier(name) {
        if (this.dbType === 'mssql') {
            return `[${name}]`;
        } else if (this.dbType === 'mysql') {
            return `\`${name}\``;
        } else {
            return `"${name}"`;
        }
    }

    /**
     * Escape SQL value.
     */
    escapeValue(value) {
        if (value === null || value === undefined) return '';
        return String(value).replace(/'/g, "''");
    }

    /**
     * Build SQL and update output.
     */
    buildAndUpdateSQL() {
        const sql = this.buildSQL();
        if (this.sqlOutput) {
            this.sqlOutput.value = sql;
        }
        this.onQueryChange(sql);
        return sql;
    }

    /**
     * Preview query results.
     */
    async previewQuery() {
        const sql = this.buildSQL();
        if (!sql) return null;

        try {
            const response = await fetch('/api/setup/schema/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: sql,
                    ...this.dbParams
                })
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Preview failed:', error);
            throw error;
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { QueryBuilder, FILTER_OPERATORS, TYPE_MAPPING };
}
