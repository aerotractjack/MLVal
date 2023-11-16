import geopandas as gpd

class GeospatialConfusionMatrix:

    def __init__(self, preds, val):
        """
        Initialize the GeospatialConfusionMatrix class with two GeoDataFrames.

        :param preds: GeoDataFrame with predictions.
        :param val: GeoDataFrame with validation data.
        """
        self.preds = preds
        self.val = val
        if self.preds.crs != self.val.crs:
            raise ValueError("The CRS of both GeoDataFrames must be the same")

    def _is_match(self, pred_poly, val_poly):
        """
        Determine if two polygons are a "match"

        :param pred_poly: Polygon from prediction
        :param val_poly: Polygon from validation
        :return: A boolean representing if polygons match
        """
        return pred_poly.intersects(val_poly)

    def true_positives(self, pred, val):
        """
        Calculate the number of true positives using Pandas methods.

        :param preds_for_class: Predicted polygons for a specific class.
        :param val_for_class: Validation polygons for a specific class.
        :return: Number of true positives.
        """

        # Initialize a set to track matched validation polygons
        matched_val_indices = set()

        def match_with_val(pred_poly):
            # Check if the prediction polygon matches with any validation polygon
            for val_index, val_poly in val.iterrows():
                if val_index in matched_val_indices:
                    continue  # Skip already matched validation polygons
                if self._is_match(pred_poly, val_poly['geometry']):
                    matched_val_indices.add(val_index)
                    return True
            return False

        # Apply the matching function to all prediction polygons and sum the true values
        tp_count = pred['geometry'].apply(match_with_val)
        if tp_count.shape[0] == 0:
            return 0
        return tp_count.sum()

    def false_positives(self, pred, val):
        """
        Calculate the number of false positives using Pandas methods.

        :param pred: GeoDataFrame with predicted polygons.
        :param val: GeoDataFrame with validation polygons.
        :return: Number of false positives.
        """

        def is_false_positive(pred_poly):
            # Check if the prediction polygon does not match with any validation polygon
            for _, val_poly in val.iterrows():
                if self._is_match(pred_poly, val_poly['geometry']):
                    return False  # This is not a false positive
            return True  # No match found, so it's a false positive

        # Apply the is_false_positive function to all prediction polygons and sum the true values
        fp_count = pred['geometry'].apply(is_false_positive)
        if fp_count.shape[0] == 0:
            return 0
        return fp_count.sum()

    def false_negatives(self, pred, val):
        return self.false_positives(val, pred)

    def confusion_matrix(self):
        """
        Calculate the confusion matrix for a specific class.

        :param class_id: The class ID for which to calculate the confusion matrix.
        :return: A dictionary representing the confusion matrix for the class.
        """
        pred, val = self.preds, self.val
        tp = self.true_positives(pred, val)
        fp = self.false_positives(pred, val)
        fn = self.false_negatives(pred, val)
        return {"TP": tp, "FP": fp, "FN": fn}

    @classmethod
    def FromGDFs(cls, preds, val):
        return cls(preds, val).confusion_matrix()
