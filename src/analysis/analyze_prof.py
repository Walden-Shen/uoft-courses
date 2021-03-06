import sys
sys.path.append('../util/')
import Database
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import argparse

PROF_QUALITY_BY_PNAME = 1 # index of DB_GETMETHOD_WITH_TWO_ARGS
DEPARTMENT_QUALITY_BY_DID = 2 # index of DB_GETMETHOD_WITH_TWO_ARGS
COURSE_EVAL_BY_CID = 5

DB_GETMETHOD_WITH_TWO_ARGS = {\
    PROF_QUALITY_BY_PNAME: Database.get_prof_quality_by_instructorFullName,\
    DEPARTMENT_QUALITY_BY_DID: Database.get_avg_prof_quality_by_department,\
    COURSE_EVAL_BY_CID: Database.get_past_eval_by_cID
} # used by __analyze_data_by_DB_GETMETHOD_DICT
   

def __analyze_data_by_DB_GETMETHOD_WITH_TWO_ARGS(get_type, dict_cursor, *args):
    """
    A generalized helper function used to return DataFrame
    """
    assert len(args) == 2
    data = DB_GETMETHOD_WITH_TWO_ARGS[get_type](dict_cursor, args[0], args[1])
    if args[1] != "St. George":
        del data['enthusiasm']
    df = pd.DataFrame(list(data.values()), columns=[args[0]], index=list(data.keys()))
    return df

def analyze_prof_quality_by_instructorFullName(dict_cursor, instructorFullName, campus):
    """
    >>> analyze_prof_quality_by_instructorFullName(dict_cursor, 'David Liu', 'St. George')
                               David Liu
    enthusiasm              4.47
    course_atmosphere       4.41
    ...
    (This is not complete)
    """
    return __analyze_data_by_DB_GETMETHOD_WITH_TWO_ARGS(PROF_QUALITY_BY_PNAME, dict_cursor, instructorFullName, campus)

def analyze_avg_prof_quality_by_department(dict_cursor, departmentID, campus):
    """
    >>> analyze_avg_prof_quality_by_department(dict_cursor, 'CSC', 'St. George')
                                CSC
    enthusiasm         3.95
    course_atmosphere  3.90
    ...
    (This is not complete)
    """
    return __analyze_data_by_DB_GETMETHOD_WITH_TWO_ARGS(DEPARTMENT_QUALITY_BY_DID, dict_cursor, departmentID, campus)

def analyze_past_eval_by_instructorFullName_and_cID(dict_cursor, instructorFullName, cID, campus):
    """
    >>> analyze_past_eval_by_instructorFullName_and_cID(dict_cursor, 'David Liu', 'CSC148', 'St. George')
                                   David Liu's CSC148
        overall_quality                          4.05
        intellectually_simulating                4.08
        homework_fairness                        4.15
        respondent_percentage                    0.37
        deeper_understanding                     4.18
        recommend_rating                         4.22
        home_quality                             4.28

    """
    course_by_prof_eval_data = Database.get_past_eval_by_instructorFullName_and_cID(dict_cursor,\
            instructorFullName, cID, campus)
    
    course_by_prof_df = pd.DataFrame(list(course_by_prof_eval_data.values()), columns =\
            ["{}'s {}".format(instructorFullName, cID)], index=list(course_by_prof_eval_data.keys()))

    return course_by_prof_df

def analyze_past_eval_by_cID(dict_cursor, cID, campus):
    """
    >>> analyze_past_eval_by_cID(dict_cursor, 'CSC265', 'St. George')
                                   CSC265
        overall_quality              4.47
        intellectually_simulating    4.68
        homework_fairness            4.42
        respondent_percentage        0.55
        deeper_understanding         4.63
        recommend_rating             4.23
        home_quality                 4.63

    """
    return __analyze_data_by_DB_GETMETHOD_WITH_TWO_ARGS(COURSE_EVAL_BY_CID, dict_cursor, cID, campus)

def analyze_past_eval_by_cID_excluding_one_prof(dict_cursor, exclusiveInstructorFullName, cID, campus):
    """
    >>> analyze_past_eval_by_cID_excluding_one_prof(dict_cursor, 'Faith Ellen', 'CSC240', 'St. George')
                      CSC240 not taught by Faith Ellen
    recommend_rating                              3.40
    deeper_understanding                          4.10
    intellectually_simulating                     4.00
    homework_fairness                             3.90
    home_quality                                  4.00
    overall_quality                               3.30
    respondent_percentage                         0.39
    """
    course_by_prof_eval_data = Database.get_past_eval_by_cID_excluding_one_prof(dict_cursor,\
            exclusiveInstructorFullName, cID, campus)
    
    course_by_prof_df = pd.DataFrame(list(course_by_prof_eval_data.values()), columns =\
            ["{} not taught by {}".format(cID, exclusiveInstructorFullName)], index=list(course_by_prof_eval_data.keys()))

    return course_by_prof_df

def analyze_course_quality_by_cID(dict_cursor, cID, campus):
    """
    First query the given course's eval data from database, then convert it into
    a DataFrame.
    """
    course_quality_by_cID = Database.get_avg_course_eval_by_cID(dict_cursor, cID, campus)

    course_quality_by_cID_df = pd.DataFrame(list(course_quality_by_cID.values()), columns =\
            ["avg course quality of {}".format(cID)], index=list(course_quality_by_cID.keys()))

    return course_quality_by_cID_df

def analyze_course_quality_by_department(dict_cursor, departmentID, campus):
    """
    First query the average evaluation data in that department from database, then convert it into
    a DataFrame.
    """
    course_quality_by_departmentID = Database.get_avg_course_eval_by_cID(dict_cursor, departmentID, campus)

    course_quality_by_departmentID_df = pd.DataFrame(list(course_quality_by_departmentID.values()), columns =\
            ["avg course quality of {} courses".format(cID[:3])], index=list(course_quality_by_departmentID.keys()))

    return course_quality_by_departmentID_df

def __get_dataframe_by_contrasting_prof_with_department(dict_cursor, instructorFullName, departmentID, campus):
    """
    Get the dataframe of selected prof's evaluation and the evaluation of avg
    profs in selected department.
    """
    df1 = analyze_prof_quality_by_instructorFullName(dict_cursor, instructorFullName, campus)
    df2 = analyze_avg_prof_quality_by_department(dict_cursor, departmentID, campus)
    df = pd.concat([df1, df2], axis=1)
    return df

def __get_dataframe_by_contrasting_prof_with_other_profs(dict_cursor, instructorFullName, cID, campus):
    """
    Get the dataframe of selected prof's evaluation and
    the avg evaluation of other profs who taught that course before.
    """
    df1 = analyze_past_eval_by_instructorFullName_and_cID(dict_cursor, instructorFullName, cID, campus)
    df2 = analyze_past_eval_by_cID_excluding_one_prof(dict_cursor, instructorFullName, cID, campus)
    df = pd.concat([df1, df2], axis=1)
    return df

def __get_dataframe_by_contrasting_course_with_other_courses(dict_cursor, cID, campus):
    """
    Get the dataframe of selected course's evaluation and
    the avg evaluation of other courses who taught in that department.
    """
    departmentID = cID[:3]
    df1 = analyze_course_quality_by_cID(dict_cursor, cID, campus)
    df2 = analyze_course_quality_by_department(dict_cursor, departmentID, campus)
    df = pd.concat([df1, df2], axis=1)
    return df

def get_figure_of_dataframe_contrasting_prof_with_department(dict_cursor, ax, instructorFullName, departmentID, campus):
    """
    Plot the prof vs avg prof in department DataFrame in python.
    """
    df = __get_dataframe_by_contrasting_prof_with_department(dict_cursor, instructorFullName, departmentID, campus)
    #return __get_figure_by_dataframe(df, title="Prof {} vs {} department".format(instructorFullName, departmentID))
    __get_figure_by_dataframe(df, ax, title="Prof {} vs {} department".format(instructorFullName, departmentID))

def get_figure_of_dataframe_contrasting_prof_with_other_profs(dict_cursor, ax, instructorFullName, cID, campus):
    """
    Plot the prof vs other profs DataFrame in python.
    """
    df = __get_dataframe_by_contrasting_prof_with_other_profs(dict_cursor, instructorFullName, cID, campus)
    __get_figure_by_dataframe(df, ax, title="Prof {} vs other profs who taught {}".format(instructorFullName, cID))

def get_figure_of_dataframe_contrasting_course_with_other_courses(dict_cursor, ax, cID, campus):
    """
    Plot the course vs other courses DataFrame in python.
    """
    df = __get_dataframe_by_contrasting_course_with_other_courses(dict_cursor, cID, campus)
    __get_figure_by_dataframe(df, ax, title="{} vs other courses taught in {} department".format(cID, cID[:3]))

def get_figure(dict_cursor, instructorFullName, cID, departmentID, campus):
    get_figure_of_dataframe_contrasting_prof_with_department(dict_cursor, instructorFullName, departmentID, campus)
    get_figure_of_dataframe_contrasting_prof_with_other_profs(dict_cursor, instructorFullName, cID, campus)
    plt.legend(loc='best')
    plt.show()

def __get_figure_by_dataframe(df, ax, title=None):
    """
    Beatify the layout of the DataFrame, add label to each bar. Then return the
    figure.
    """
    try:
        new_ax = df.plot(ax=ax, kind='bar', rot=0, alpha=0.6, title=title, figsize=(18, 11.12), fontsize=14)
        new_ax.legend(loc='best', fancybox=True, framealpha=0.5)
        for p in new_ax.patches:
            new_ax.annotate(str(p.get_height()), (p.get_x() * 1.005, p.get_height() * 1.005))
    except TypeError as e:
        print("Unable to plot. Please check your data", file=sys.stdout)

def convert_figure_to_html(fig):
    """
    Convert the figure into a png in base64 form
    """
    sio = BytesIO()
    fig.savefig(sio, format='png')
    data = base64.encodebytes(sio.getvalue()).decode()
    return data.replace('\n', '')
    #return '<img src="data:image/png;base64,{}">'.format(data.replace('\n', ''))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--plot', help = "Plot the graph in GUI mod (if this flag is not set on, an html img tag will be printed to stdout)", action = "store_true")
    parser.add_argument('instructor', help = "The full name of instructor")
    parser.add_argument('courseID', help = "The id of course, e.g., CSC240")
    parser.add_argument('campus', help = "The campus where the instructor stays")
    args = parser.parse_args()

    instructorFullName = args.instructor
    cID = args.courseID
    department = cID[0: 3]
    campus = args.campus

    connection = Database.get_connection_with_dict_cursor('../../database.info', 'uoftcourses')
    dict_cursor = connection.cursor()

    fig, axes = plt.subplots(nrows=3, ncols=1)

    get_figure_of_dataframe_contrasting_prof_with_department(dict_cursor, axes[0], instructorFullName, department, campus)
    get_figure_of_dataframe_contrasting_prof_with_other_profs(dict_cursor, axes[1], instructorFullName, cID, campus)
    get_figure_of_dataframe_contrasting_course_with_other_courses(dict_cursor, axes[2], cID, campus)


    fig = plt.gcf()
    fig.tight_layout()
    if args.plot:
        plt.show()
    else:
        print(convert_figure_to_html(fig))
        sys.stdout.flush()
