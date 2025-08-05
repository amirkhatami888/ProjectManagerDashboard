/**
 * Jalali Datepicker Initialization
 * This script initializes Persian date pickers across the application
 */
class JalaliDatePicker {
    constructor() {
        this.persianMonths = [
            'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
        ];
        
        this.persianDays = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'];
        
        this.currentInput = null;
        this.currentPicker = null;
        this.currentDate = this.getCurrentPersianDate();
        
        this.init();
    }
    
    init() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('calendar-icon')) {
                this.showPicker(e.target);
            } else if (!e.target.closest('.jalali-datepicker')) {
                this.hidePicker();
            }
        });
    }

    getCurrentPersianDate() {
        const now = new Date();
        return this.gregorianToPersian(now.getFullYear(), now.getMonth() + 1, now.getDate());
    }
    
    showPicker(icon) {
        this.hidePicker();
        
        const inputId = icon.getAttribute('data-input');
        this.currentInput = document.getElementById(inputId);
        
        if (!this.currentInput) return;
        
        const picker = this.createPicker();
        this.currentPicker = picker;
        
        document.body.appendChild(picker);
        this.positionPicker(icon, picker);
        
        const inputValue = this.currentInput.value;
        if (inputValue) {
            const parts = inputValue.split('/');
            if (parts.length === 3) {
                this.currentDate = {
                    year: parseInt(parts[0]),
                    month: parseInt(parts[1]),
                    day: parseInt(parts[2])
                };
        }
        }
        
        this.updatePicker();
    }
    
    hidePicker() {
        if (this.currentPicker) {
            this.currentPicker.remove();
            this.currentPicker = null;
            this.currentInput = null;
        }
    }
    
    createPicker() {
        const picker = document.createElement('div');
        picker.className = 'jalali-datepicker';
        
        picker.innerHTML = `
            <div class="header">
                <button type="button" class="nav-btn prev-year">‹‹</button>
                <button type="button" class="nav-btn prev-month">‹</button>
                <div class="month-year"></div>
                <button type="button" class="nav-btn next-month">›</button>
                <button type="button" class="nav-btn next-year">››</button>
            </div>
            <div class="calendar">
                <div class="weekdays"></div>
                <div class="days"></div>
            </div>
        `;
        
        this.attachPickerEvents(picker);
        return picker;
    }
    
    attachPickerEvents(picker) {
        picker.querySelector('.prev-year').onclick = () => {
            this.currentDate.year--;
            this.updatePicker();
        };
        
        picker.querySelector('.prev-month').onclick = () => {
            this.currentDate.month--;
            if (this.currentDate.month < 1) {
                this.currentDate.month = 12;
                this.currentDate.year--;
            }
            this.updatePicker();
        };
        
        picker.querySelector('.next-month').onclick = () => {
            this.currentDate.month++;
            if (this.currentDate.month > 12) {
                this.currentDate.month = 1;
                this.currentDate.year++;
            }
            this.updatePicker();
        };
        
        picker.querySelector('.next-year').onclick = () => {
            this.currentDate.year++;
            this.updatePicker();
        };
    }
    
    updatePicker() {
        if (!this.currentPicker) return;
        
        const monthYear = this.currentPicker.querySelector('.month-year');
        monthYear.textContent = `${this.persianMonths[this.currentDate.month - 1]} ${this.currentDate.year}`;
        
        this.updateWeekdays();
        this.updateDays();
    }
    
    updateWeekdays() {
        const weekdays = this.currentPicker.querySelector('.weekdays');
        weekdays.innerHTML = '';
        
        this.persianDays.forEach(day => {
            const dayEl = document.createElement('div');
            dayEl.className = 'weekday';
            dayEl.textContent = day;
            weekdays.appendChild(dayEl);
        });
    }
    
    updateDays() {
        const days = this.currentPicker.querySelector('.days');
        days.innerHTML = '';
        
        const daysInMonth = this.getDaysInPersianMonth(this.currentDate.year, this.currentDate.month);
        const firstDayOfWeek = this.getFirstDayOfPersianMonth(this.currentDate.year, this.currentDate.month);
        
        // Add empty cells for days before month start
        for (let i = 0; i < firstDayOfWeek; i++) {
            const dayEl = document.createElement('div');
            dayEl.className = 'day other-month';
            days.appendChild(dayEl);
        }
        
        // Add days of current month
        for (let day = 1; day <= daysInMonth; day++) {
            const dayEl = document.createElement('div');
            dayEl.className = 'day';
            dayEl.textContent = day;
            
            // Check if it's today
            const today = this.getCurrentPersianDate();
            if (this.currentDate.year === today.year && 
                this.currentDate.month === today.month && 
                day === today.day) {
                dayEl.classList.add('today');
            }
            
            dayEl.onclick = () => this.selectDate(day);
            days.appendChild(dayEl);
        }
    }
    
    selectDate(day) {
        const selectedDate = `${this.currentDate.year}/${this.currentDate.month.toString().padStart(2, '0')}/${day.toString().padStart(2, '0')}`;
        this.currentInput.value = selectedDate;
        
        // Convert to Gregorian and set hidden field
        const gregorian = this.persianToGregorian(this.currentDate.year, this.currentDate.month, day);
        const hiddenField = document.getElementById(this.currentInput.id.replace('_display', '_gregorian'));
        if (hiddenField) {
            hiddenField.value = `${gregorian.year}-${gregorian.month.toString().padStart(2, '0')}-${gregorian.day.toString().padStart(2, '0')}`;
        }
        
        this.hidePicker();
        }

    positionPicker(icon, picker) {
        const rect = icon.getBoundingClientRect();
        picker.style.position = 'absolute';
        picker.style.top = (rect.bottom + window.scrollY + 5) + 'px';
        picker.style.left = (rect.left + window.scrollX - 250) + 'px';
        
        // Adjust if picker goes off screen
        const pickerRect = picker.getBoundingClientRect();
        if (pickerRect.right > window.innerWidth) {
            picker.style.left = (window.innerWidth - pickerRect.width - 10) + 'px';
        }
        if (pickerRect.left < 0) {
            picker.style.left = '10px';
        }
    }
    
    getDaysInPersianMonth(year, month) {
        if (month <= 6) return 31;
        if (month <= 11) return 30;
        return this.isPersianLeapYear(year) ? 30 : 29;
    }
    
    isPersianLeapYear(year) {
        const breaks = [
            -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
            1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178
        ];
        
        let gy = year + 1595;
        let leap = -14;
        let jp = breaks[0];
        
        let jump = 0;
        for (let j = 1; j <= 19; j++) {
            let jm = breaks[j];
            jump = jm - jp;
            if (year < jm) break;
            leap += Math.floor(jump / 33) * 8 + Math.floor((jump % 33) / 4);
            jp = jm;
        }
        
        let n = year - jp;
        if (n < jump) {
            leap += Math.floor(n / 33) * 8 + Math.floor((n % 33 + 3) / 4);
            if ((jump % 33) === 4 && (jump - n) === 4) leap++;
        }
        
        return (leap + 4) % 33 < 5;
    }
    
    getFirstDayOfPersianMonth(year, month) {
        const gregorian = this.persianToGregorian(year, month, 1);
        const date = new Date(gregorian.year, gregorian.month - 1, gregorian.day);
        return (date.getDay() + 1) % 7; // Adjust for Persian week starting on Saturday
    }
    
    gregorianToPersian(gy, gm, gd) {
        const g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
        
        if (gy <= 1600) {
            let jy = 0;
            gy -= 621;
        } else {
            let jy = 979;
            gy -= 1600;
        }
        
        if (gm > 2) {
            gy2 = gy + 1;
        } else {
            gy2 = gy;
        }
        
        let days = (365 * gy) + (Math.floor((gy2 + 3) / 4)) + (Math.floor((gy2 + 99) / 100)) - 
                  (Math.floor((gy2 + 399) / 400)) - 80 + gd + g_d_m[gm - 1];
        
        let jy = -1029;
        let jp = 0;
        
        while (jp < days) {
            jy++;
            jp += this.isPersianLeapYear(jy) ? 366 : 365;
        }
        
        if (jp - days >= 0) {
            jp -= this.isPersianLeapYear(jy) ? 366 : 365;
        } else {
            jy++;
        }
        
        days -= jp;
        
        let jm = 0;
        while (jm < 12 && days >= this.getDaysInPersianMonth(jy, jm + 1)) {
            days -= this.getDaysInPersianMonth(jy, jm + 1);
            jm++;
        }
        
        return {
            year: jy,
            month: jm + 1,
            day: days + 1
        };
    }
    
    persianToGregorian(jy, jm, jd) {
        let gy = jy <= 979 ? 621 : 1600;
        jy = jy <= 979 ? jy : jy - 979;
        
        let days = (365 * jy) + (Math.floor(jy / 33) * 8) + 
                  (Math.floor(((jy % 33) + 3) / 4)) + 78 + jd;
        
        if (jm < 7) {
            days += (jm - 1) * 31;
        } else {
            days += ((jm - 7) * 30) + 186;
        }
        
        let gy2 = gy + 1600;
        let gd = days - 79;
        
        let cycle = Math.floor(gd / 146097);
        gd = gd % 146097;
        
        let cyear = 0;
        if (gd >= 36525) {
            gd--;
            cyear = Math.floor(gd / 36524);
            if (cyear > 3) cyear = 3;
            gd -= cyear * 36524;
        }
        
        let year = Math.floor(gd / 365);
        if (year > 3) year = 3;
        
        gy = gy2 + (cycle * 400) + (cyear * 100) + year * 1;
        gd = gd - (year * 365);
        
        if ((gy % 4 === 0 && gy % 100 !== 0) || (gy % 400 === 0)) {
            let leap = 1;
        } else {
            let leap = 0;
        }
        
        const sal_a = [0, 31, (59 + leap), (90 + leap), (120 + leap), (151 + leap),
                      (181 + leap), (212 + leap), (243 + leap), (273 + leap), 
                      (304 + leap), (334 + leap), (365 + leap)];
        
        let gm = 0;
        while (gm < 13 && gd >= sal_a[gm]) {
            gm++;
                }
        
        if (gm > 1) {
            gd = gd - sal_a[gm - 1];
        }
        
        return {
            year: gy,
            month: gm,
            day: gd + 1
        };
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    if (typeof jQuery !== 'undefined' && typeof persianDate !== 'undefined' && $.fn.persianDatepicker) {
        new JalaliDatePicker();
    } else {
        console.error('jQuery, persianDate, or persianDatepicker is not loaded. JalaliDatePicker not initialized.');
    }
}); 