from collections import defaultdict, Counter
from typing import List, Tuple
import pandas as pd
import numpy as np


from .datasets import Metric, Dataset


class Dataview(Dataset): #TODO determine where to put queries

    def __init__(self, status_list: List[str], label_map: dict, master_dataset_path: str):
        super().__init__(status_list, label_map)
        try:
            self.master_df = pd.read_csv(master_dataset_path, index_col = 'object_id')
            
        except ValueError:
            self.master_df = pd.read_csv(master_dataset_path, index_col = 'o.CNH_id')
            
        print(f"{master_dataset_path} succeeded")
    
    def summary_pd_query(self, query: dict, metrics: str, threshold_linspace: np.linspace = np.linspace(0.5, 1, 51,True)) -> Tuple[pd.DataFrame, pd.DataFrame]: # gets numbers, not samples
        """
        Query for information in a dataframe; computes metrics at every value in threshold_linspace. 


        Query format: {status : str,
             family: [vals],
             order: [vals], 
             {status} Prediction: True/False,
             {status} Prediction Confidence: np.linspace,
        metrics: ['Accuracy', 'F1-score','Precision', 'Recall',True Positive', 'False Positive', 'True Negative', 'False Negative']}

        Returns:
            base_metric_df: the summary_df of metrics against threshold (incremented)
            mask_df: individual item mask
        """

        # the index= parameter is what makes this all work
        mask = pd.Series([False] * len(self.master_df), index = self.master_df.index)

        # status filter


        # family filter
        # print(query["family"])
        # print(self.master_df[self.master_df["family"].isin(query["family"])])
        if len(query['family'])> 1:
            mask = (mask) | (self.master_df["family"].isin(query["family"]))
        elif query['family'] == ['All Families']:
            mask = pd.Series([True] * len(self.master_df), index = self.master_df.index)
        elif len(query['family']) == 1:
            mask = (mask) | (self.master_df["family"] == query['family'])
        # print(f"{Counter(mask)=}")

        # order filter
        # TODO: remove order as a necessary query step
        if len(query['order']) > 1:
            mask = (mask) | (self.master_df["order"].isin(query["order"]))
        elif query['order'] == ['All Orders']:
            mask = pd.Series([True] * len(self.master_df), index = self.master_df.index)
        elif len(query['order']) == 1:
            mask = (mask) | (self.master_df["order"] == query['order'])
        # print(f"{Counter(mask)=}")

        base_metric_df = pd.DataFrame(index=np.linspace(0.5,1,51,True))
        
        full_mask = mask.copy()


        for status in query['status']:
            # status filter
            # print(f"{status} base mask: {Counter(mask)}")
            status_mask = (mask) & (self.master_df[f"{status} Prediction"].notnull())
            # print(f"{Counter(status_mask)=}")
            # print(f"{status} status mask: {Counter(status_mask)}")
            full_mask = (full_mask) & (status_mask)
            original_length = Counter(status_mask)[True]
            # set correct metric status
            full_metrics = {"Accuracy %": (Metric.accuracy, {"status": status}),
                            "Capture %": (Metric.capture, {"status": status, "original_length": original_length}),
                            "Count": (Metric.count_samples,{"status": status}),
                            # "F1 Score": (Metric.f1, {"status": status}),
                            # "Precision": (Metric.precision, {"status": status}),
                            # "Recall": (Metric.recall, {"status": status}),
                            "Ground Truth Positive %": (Metric.percentage_valence, {"status": status, "valence": 0}),
                            "Ground Truth Negative %":(Metric.percentage_valence, {"status": status, "valence": 1}),
                            "Ground Truth Undetermined %": (Metric.percentage_valence, {"status": status, "valence": 2}),
                            "True Positive %": (Metric.pred_type_percentage, {"status": str, "pred_valence": True, "gt_valence": True}),
                            "False Positive %": (Metric.pred_type_percentage, {"status": str, "pred_valence": True, "gt_valence": False}),
                            "False Negative %": (Metric.pred_type_percentage, {"status": str, "pred_valence": False, "gt_valence": True}),
                            "True Negative %": (Metric.pred_type_percentage, {"status": str, "pred_valence": False, "gt_valence": False})}


            
            # print(f"{status} length: {len(self.master_df[status_mask])}")
            metric_df = self.threshold_range(self.master_df[status_mask], [status], threshold_linspace, [full_metrics[metric] for metric in metrics])
            base_metric_df = base_metric_df.join(metric_df)



        mask_df = self.master_df[full_mask]

        
        return base_metric_df, mask_df


    def stats_by_taxa(self, taxa_col, status_list, metrics: List[str]):
        """
        Computes statistics, grouped by taxa

        :param: df: the dataframe
        :param: taxa_col: the name of the column to use as the groupby
        :param stat__func_nlist: statistics to compute 

        """ 
        taxa_list = self.master_df.loc[:, taxa_col].unique()
        taxa_result_list = []
        for taxa in taxa_list:
            taxa_df = self.master_df[self.master_df[taxa_col] == taxa]
            status_dict = {}
            for status in status_list:
                original_length = len(taxa_df)
                full_metrics = {"Accuracy %": (Metric.accuracy, {"status": status}),
                        "Capture %": (Metric.capture, {"status": status, "original_length": original_length}),
                        "Count": (Metric.count_samples,{"status": status}),
                        # "F1 Score": (Metric.f1, {"status": status}),
                        # "Precision": (Metric.precision, {"status": status}),
                        # "Recall": (Metric.recall, {"status": status}),
                        "Ground Truth Positive %": (Metric.percentage_valence, {"status": status, "valence": 0}),
                        "Ground Truth Negative %":(Metric.percentage_valence, {"status": status, "valence": 1}),
                        "Ground Truth Undetermined %": (Metric.percentage_valence, {"status": status, "valence": 2}),
                        "True Positive %": (Metric.pred_type_percentage, {"status": str, "pred_valence": True, "gt_valence": True}),
                        "False Positive %": (Metric.pred_type_percentage, {"status": str, "pred_valence": True, "gt_valence": False}),
                        "False Negative %": (Metric.pred_type_percentage, {"status": str, "pred_valence": False, "gt_valence": True}),
                        "True Negative %": (Metric.pred_type_percentage, {"status": str, "pred_valence": False, "gt_valence": False})}


                status_dict.update(self.threshold_single(taxa_df, status, 0.95, [full_metrics[metric] for metric in metrics]))

            taxa_result_list.append(status_dict)
        return pd.DataFrame.from_records(taxa_result_list, index=taxa_list)
    


    def sample_pd_query(self, df: pd.DataFrame, status_list: List[str], threshold: float) -> pd.DataFrame: # gets individual samples
        """
        This is at least 5x slower than using sql, but using sql adds overheard for going from pandas to sql because the logic cannot be moved out of pandas



        Query format: (default_dict)
            {status : str,
             family: [vals],
             order: [vals], 
             {status} Prediction: True/False/None,
             {status} Prediction Confidence: float,
             confusion_state: ['True Positive', 'False Positive', 'True Negative', 'False Negative']}
        """
    


        # we want to OR everything!
        mask = pd.Series([False] * len(df), index = df.index)

        for status in status_list:
            mask = (mask) | (df[f"{status} Prediction Confidence"] > threshold)
        
        print(len(df))
        mask_df = df[mask]
        print(mask_df.columns)
        print(f"len of mask_df: {len(mask_df)}")
        try:
            status_cols = []
            for status in status_list:
                status_cols.extend([f"{status} Prediction", f"{status} Prediction Confidence", f"{status} Ground Truth"])
            col_list = ["sci_name", "family", "order"] + status_cols
            return mask_df[col_list]
        except KeyError:
            status_cols = []
            for status in status_list:
                status_cols.extend([f"{status} Prediction", f"{status} Prediction Confidence"])
            col_list = ["sci_name", "family", "order"] + status_cols
            return mask_df[col_list]


        


    
    



        


        # # move this below
        # if query['status'] != "All" and len(query['status']) > 0:
        #     mask = mask & (self.master_df[f"{query['status']} Prediction Confidence"] > query["confidence"])

