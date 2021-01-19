$(document).ready(function () {
    // Handle Metric Selection
    $('.selection').click(function () {
        let element = $(this);
        if (element.hasClass('isSelected')) return;
        $('.selection.isSelected').removeClass('isSelected');
        element.addClass('isSelected');
        let metric = element.parent().attr('class').split(/\s+/)[2];
        setMetric(metric);
    })

    $('.back-to-all-data').click(function () {
        updateMetricsForGermany();
    })
})

const UpdateConfig = {
    COUNTY: 'county',
    TOTAL: 'total',
    GENERAL: 'general'
}
Object.freeze(UpdateConfig)

let selectedConfig = UpdateConfig.TOTAL;

function initDashboard() {
    $('.selected-location').html('Deutschland');
    selectedConfig = UpdateConfig.TOTAL;
    updateMetricElements();
    $('.metric-date').html('Stand: ' + getDateInFormat(selectedDate));
    $('.back-to-all-data').css('opacity', '0');
}

function updateMetricsForSelectedCounty(county) {
    $('.selected-location').html(county['GEN']);
    selectedConfig = UpdateConfig.COUNTY;
    updateMetricElements(county);
    $('.back-to-all-data').css('opacity', '1');
    setCounty(county['AGS']);
}

function updateMetricsForGermany() {
    $('.selected-location').html('Deutschland');
    selectedConfig = UpdateConfig.TOTAL;
    updateMetricElements();
    $('.back-to-all-data').css('opacity', '0');
    setCounty(null);
    removeSelection();
}

function updateMetrics() {
    selectedConfig = UpdateConfig.GENERAL;
    updateMetricElements();
}

function removeSelection() {
    let prevElement = $('#map').find('.selected-county');
    if (prevElement[0]) {
        prevElement[0].classList.remove('selected-county');
    }
}

function getDateInFormat(date) {
    let parseDateFromData = d3.timeParse('%Y/%m/%d');
    let readableDateParser = d3.timeFormat('%d.%m.%Y');
    return readableDateParser(parseDateFromData(date));
}

function updateMetricElements(county) {
    let config;
    switch (selectedConfig) {
        case UpdateConfig.COUNTY:
            config = county['AGS'];
            break;
        case UpdateConfig.TOTAL:
            config = 'all'
            break;
        case UpdateConfig.GENERAL:
            config = selectedCountyId || 'all';
            break;
        default:
            config = selectedCountyId || 'all';
    }
    let newCases = getNumberWithCommas(data[selectedDate][config][Metric.NEW_CASES]);
    let totalCases = getNumberWithCommas(data[selectedDate][config][Metric.TOTAL_CASES]);
    let newDeaths = getNumberWithCommas(data[selectedDate][config][Metric.NEW_DEATHS]);
    let totalDeaths = getNumberWithCommas(data[selectedDate][config][Metric.TOTAL_DEATHS]);
    let caseIncidence = (Math.round(data[selectedDate][config][Metric.CASE_INCIDENCE] * 10) / 10).toString().replace(/\./g, ',');
    let deathIncidence = (Math.round(data[selectedDate][config][Metric.DEATH_INCIDENCE] * 10) / 10).toString().replace(/\./g, ',');

    $('.metric.newCases').find('.metric-number').html(newCases === null ? 'keine Daten' : newCases);
    $('.metric.totalCases').find('.metric-number').html(totalCases === null ? 'keine Daten' : totalCases);
    $('.metric.newDeaths').find('.metric-number').html(newDeaths === null ? 'keine Daten' : newDeaths);
    $('.metric.totalDeaths').find('.metric-number').html(totalDeaths === null ? 'keine Daten' : totalDeaths);
    $('.metric.caseIncidence').find('.metric-number').html(caseIncidence === null ? 'keine Daten' : caseIncidence);
    $('.metric.deathIncidence').find('.metric-number').html(deathIncidence === null ? 'keine Daten' : deathIncidence);

    function getNumberWithCommas(x) {
        return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    }
}

var germanFormatters = d3.timeFormatDefaultLocale({
    "date": "%d.%m.%Y",
    "days": ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"],
    "shortDays": ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"],
    "months": ["Jannuar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "shortMonths": ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
});

var customTimeFormat = germanFormatters.timeFormat.multi([
    ["%B", function(d) { return d.getMonth(); }],
    ["%Y", function() { return true; }]
]);