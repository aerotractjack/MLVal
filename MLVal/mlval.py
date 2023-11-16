import geopandas as gpd
import pandas as pd
import json

from . import integration 
from .confusion_matrix import GeospatialConfusionMatrix

class MLValReport:

    def __init__(self, src_img_path, validation_data_paths, prediction_path, mlval_report_path):
        self.src_img_path = src_img_path
        self.val_paths = validation_data_paths
        self.pred_path = prediction_path
        self.report_path = mlval_report_path
        self.preds = gpd.read_file(self.pred_path, driver="GeoJSON")

    def _fix_class_ids_col_name(self, val_gdf):
        # helper method to make sure class_id column is named consistently
        if 'class_ids' in val_gdf:
            val_gdf['class_id'] = val_gdf['class_ids']
            del val_gdf['class_ids']
        return val_gdf

    def _points_within_aoi(self, i):
        # mask and return the predicted and validated points from within
        # an area of interest
        aoi_path = self.val_paths['aoi'][i]
        aoi_gdf = gpd.read_file(aoi_path, driver="GeoJSON")
        aoi_polygon = aoi_gdf.iloc[0].geometry
        val_path = self.val_paths['points'][i]
        val_gdf = gpd.read_file(val_path, driver="GeoJSON")
        val_gdf = self._fix_class_ids_col_name(val_gdf)
        preds = self.preds
        if 'class_id' not in preds:
            preds['class_id'] = []
        if 'class_id' not in val_gdf:
            val_gdf['class_id'] = []
        preds['class_id'] = preds['class_id'].astype(int)
        val_gdf['class_id'] = val_gdf['class_id'].astype(int)
        return preds[preds.geometry.within(aoi_polygon)], val_gdf

    def _aoi_confusion_matrix(self, i):
        # calculate a confusion matrix for each class present in pred and val
        preds_gdf, val_gdf = self._points_within_aoi(i)
        class_cm = []
        unq = sorted(set(preds_gdf['class_id']) | set(val_gdf['class_id']))
        for c in unq:
            preds_gdf_c = preds_gdf[preds_gdf['class_id'] == c]
            val_gdf_c = val_gdf[val_gdf['class_id'] == c]
            cm = GeospatialConfusionMatrix.FromGDFs(preds_gdf_c, val_gdf_c)
            cm['class_id'] = c
            class_cm.append(cm)
        return class_cm

    def sum_confusion_matrices(self, confusion_matrices):
        # sum the confusion matrices for each AOI/class to get the 
        # metrics for the whole stand
        df = pd.DataFrame(confusion_matrices)
        # df2 = df.copy()
        # df2['class_id'] = [1] * df2.shape[0]
        # df = pd.concat((df, df2))
        class_cm = df.groupby('class_id').sum().reset_index().to_dict("records")
        total_cm = df[["TP", "FP", "FN"]].sum().to_dict()
        return class_cm, total_cm

    def confusion_matrix_accuracy(self, class_confusion_matrices):
        class_acc = {}
        for confusion_matrix in class_confusion_matrices:
            tp = confusion_matrix["TP"]
            fp = confusion_matrix["FP"]
            fn = confusion_matrix["FN"]
            total = tp + fp + fn
            acc = 0
            if total > 0:
                acc = tp / total
            class_acc[int(confusion_matrix["class_id"])] = acc
        return class_acc

    def report(self):
        cms = []
        for i in range(len(self.val_paths['aoi'])):
            cm = self._aoi_confusion_matrix(i)    
            cms.extend(cm)
        class_cm, total_cm = self.sum_confusion_matrices(cms)
        class_acc = self.confusion_matrix_accuracy(class_cm)
        report = {
            "class_confusion_matrix": class_cm,
            "total_confusion_matrix": total_cm,
            "class_acc": class_acc
        }
        with open(self.report_path, "w") as fp:
            fp.write(json.dumps(report, indent=4))
        return report 

    @classmethod
    def FromPaths(cls, src_img_path, validation_data_paths, prediction_path, mlval_report_path):
        self = cls(src_img_path, validation_data_paths, prediction_path, mlval_report_path)
        return self

    @classmethod
    def FromIDs(cls, client_id, project_id, stand_id):
        src_img_path = integration.get_src_img_path(client_id, project_id, stand_id)['filepath']
        val_paths = integration.get_val_paths(client_id, project_id, stand_id)['filepath']
        pred_path = integration.get_prediction_path(client_id, project_id, stand_id)['filepath']
        report_path = integration.get_mlval_report_path(client_id, project_id, stand_id)['filepath']
        self = cls(src_img_path, val_paths, pred_path, report_path)
        return self