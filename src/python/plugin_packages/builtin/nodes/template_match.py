"""
模板匹配节点 - 基于预生成模板在图像中搜索匹配的轮廓

提供完整的模板匹配功能，包括：
- 支持多种匹配算法（Hu矩、Shape Context、Hausdorff）
- 相似度阈值控制和多结果输出
- 按相似度排序并限制返回数量
- 标注图像绘制（不同排名不同颜色）
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class TemplateMatchNode(BaseNode):
    """
    模板匹配节点
    
    基于预生成的模板数据在输入图像中搜索匹配的轮廓。
    
    功能特性：
    - 支持Hu矩、Shape Context、Hausdorff三种匹配算法
    - 提供相似度阈值过滤和多结果输出
    - 按相似度降序排序并限制返回数量
    - 可视化标注匹配结果（不同排名不同颜色）
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'match_location'
    NODE_NAME = '模板匹配'
    
    # 资源等级声明
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(TemplateMatchNode, self).__init__()
        
        # 输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_input('模板数据', color=(255, 255, 100))
        
        # 输出端口
        self.add_output('标注图像', color=(100, 255, 100))
        self.add_output('匹配数量', color=(100, 100, 255))
        self.add_output('匹配结果', color=(255, 255, 100))
        
        # 创建自定义参数容器控件
        self._param_container = ParameterContainerWidget(self.view, 'template_params', '')
        
        # 匹配算法参数
        self._param_container.add_combobox('algorithm', '匹配算法',
                                          items=['hu_moments', 'hausdorff', 'shape_context'])
        
        # 筛选条件参数
        self._param_container.add_spinbox('similarity_threshold', '相似度阈值', value=0.8, min_value=0.0, max_value=1.0, double=True)
        self._param_container.add_spinbox('min_area', '最小面积', value=0, min_value=0, max_value=999999)
        self._param_container.add_spinbox('max_area', '最大面积', value=999999, min_value=1, max_value=999999)
        self._param_container.add_spinbox('max_results', '最大匹配数', value=10, min_value=1, max_value=100)
        
        # 显示选项参数
        self._param_container.add_checkbox('draw_contours', '绘制轮廓', state=True)
        self._param_container.add_checkbox('draw_centroids', '绘制质心', state=True)
        self._param_container.add_checkbox('annotate_similarity', '标注相似度', state=True)
        
        # 颜色配置（第1名）
        self._param_container.add_spinbox('rank1_color_r', '第1名R', value=0, min_value=0, max_value=255)
        self._param_container.add_spinbox('rank1_color_g', '第1名G', value=255, min_value=0, max_value=255)
        self._param_container.add_spinbox('rank1_color_b', '第1名B', value=0, min_value=0, max_value=255)
        
        # 颜色配置（第2名）
        self._param_container.add_spinbox('rank2_color_r', '第2名R', value=255, min_value=0, max_value=255)
        self._param_container.add_spinbox('rank2_color_g', '第2名G', value=255, min_value=0, max_value=255)
        self._param_container.add_spinbox('rank2_color_b', '第2名B', value=0, min_value=0, max_value=255)
        
        # 设置值变化回调
        self._param_container.set_value_changed_callback(self._on_param_changed)
        
        # 添加到节点
        self.add_custom_widget(self._param_container, tab='properties')
    
    def _on_param_changed(self, name, value):
        """参数值变化回调"""
        self.set_property(name, str(value))
    
    def _check_shape_context_availability(self):
        """
        检查Shape Context算法是否可用
        
        Returns:
            bool: 是否可用
        """
        try:
            import cv2.xfeatures2d
            return True
        except ImportError:
            self.log_warning("⚠️ Shape Context算法需要安装opencv-contrib-python")
            self.log_info("💡 安装命令: pip install opencv-contrib-python")
            return False
    
    def _match_hu_moments(self, template_data, contour):
        """
        使用Hu矩进行匹配
        
        Args:
            template_data: 模板数据字典
            contour: 候选轮廓
            
        Returns:
            float: 相似度（0-1，越大越相似）
        """
        try:
            # 提取模板Hu矩
            template_hu = np.array(template_data['template_data']['hu_moments'])
            
            # 计算候选轮廓Hu矩
            moments = cv2.moments(contour)
            candidate_hu = cv2.HuMoments(moments).flatten()
            
            # 计算欧氏距离
            distance = np.linalg.norm(template_hu - candidate_hu)
            
            # 转换为相似度（距离越小，相似度越高）
            similarity = 1.0 / (1.0 + distance)
            
            return similarity
        
        except Exception as e:
            self.log_error(f"Hu矩匹配失败: {e}")
            return 0.0
    
    def _match_shape_context(self, template_data, contour):
        """
        使用Shape Context进行匹配
        
        Args:
            template_data: 模板数据字典
            contour: 候选轮廓
            
        Returns:
            float: 相似度（0-1，越大越相似）
        """
        try:
            # 检查依赖
            if not self._check_shape_context_availability():
                self.log_error("❌ Shape Context不可用，请安装opencv-contrib-python")
                return 0.0
            
            import cv2.xfeatures2d
            
            # 获取采样点
            descriptor = template_data['template_data']['shape_context_descriptor']
            template_points = np.array(descriptor['sampled_points'], dtype=np.float32)
            
            # 采样候选轮廓点
            n_points = descriptor['n_points']
            if len(contour) > n_points:
                indices = np.linspace(0, len(contour) - 1, n_points, dtype=int)
                candidate_points = contour[indices].reshape(-1, 2).astype(np.float32)
            else:
                candidate_points = contour.reshape(-1, 2).astype(np.float32)
            
            # 创建Shape Context距离提取器
            sc_extractor = cv2.xfeatures2d.createShapeContextDistanceExtractor()
            
            # 设置参数
            sc_extractor.setAngularBins(descriptor['n_angular_bins'])
            sc_extractor.setRadialBins(descriptor['n_radial_bins'])
            sc_extractor.setInnerRadius(descriptor['inner_radius'])
            sc_extractor.setOuterRadius(descriptor['outer_radius'])
            
            # 计算距离
            distance = sc_extractor.computeDistance(template_points, candidate_points)
            
            # 转换为相似度
            similarity = 1.0 / (1.0 + distance)
            
            return similarity
        
        except Exception as e:
            self.log_error(f"Shape Context匹配失败: {e}")
            import traceback
            traceback.print_exc()
            return 0.0
    
    def _match_hausdorff(self, template_data, contour):
        """
        使用Hausdorff距离进行匹配
        
        Args:
            template_data: 模板数据字典
            contour: 候选轮廓
            
        Returns:
            float: 相似度（0-1，越大越相似）
        """
        try:
            # 获取模板点集
            template_points = np.array(template_data['template_data']['contour_points'], dtype=np.float32)
            
            # 获取候选轮廓点集
            candidate_points = contour.reshape(-1, 2).astype(np.float32)
            
            # 创建Hausdorff距离提取器
            hd_extractor = cv2.createHausdorffDistanceExtractor()
            
            # 计算距离
            distance = hd_extractor.computeDistance(template_points, candidate_points)
            
            # 归一化处理
            normalization_factor = template_data['template_data'].get('normalization_factor', 1.0)
            normalized_distance = distance / normalization_factor if normalization_factor > 0 else distance
            
            # 转换为相似度
            similarity = 1.0 / (1.0 + normalized_distance)
            
            return similarity
        
        except Exception as e:
            self.log_error(f"Hausdorff匹配失败: {e}")
            return 0.0
    
    def _compute_centroid(self, contour):
        """
        计算轮廓质心
        
        Args:
            contour: 轮廓点集
            
        Returns:
            dict: 质心坐标 {'x': float, 'y': float}
        """
        moments = cv2.moments(contour)
        
        if moments['m00'] == 0:
            return {'x': 0, 'y': 0}
        
        cx = moments['m10'] / moments['m00']
        cy = moments['m01'] / moments['m00']
        
        return {'x': round(cx, 2), 'y': round(cy, 2)}
    
    def _get_color_by_rank(self, rank):
        """
        根据排名获取颜色
        
        Args:
            rank: 排名（从1开始）
            
        Returns:
            tuple: BGR颜色元组
        """
        params = self._param_container.get_values_dict()
        
        if rank == 1:
            r = int(params.get('rank1_color_r', 0))
            g = int(params.get('rank1_color_g', 255))
            b = int(params.get('rank1_color_b', 0))
            return (b, g, r)  # OpenCV使用BGR顺序
        elif rank == 2:
            r = int(params.get('rank2_color_r', 255))
            g = int(params.get('rank2_color_g', 255))
            b = int(params.get('rank2_color_b', 0))
            return (b, g, r)
        else:
            # 第3名及以后使用橙色
            return (0, 165, 255)  # BGR格式的橙色
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: [输入图像, 模板数据]
            
        Returns:
            dict: 包含标注图像、匹配数量和匹配结果的字典
        """
        try:
            # Step 1: 验证输入
            if not inputs or len(inputs) < 2:
                self.log_error("❌ 输入不完整，需要输入图像和模板数据")
                return {
                    '标注图像': None,
                    '匹配数量': 0,
                    '匹配结果': []
                }
            
            input_image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            template_data = inputs[1][0] if isinstance(inputs[1], list) else inputs[1]
            
            if input_image is None:
                self.log_error("❌ 未接收到输入图像")
                return {
                    '标注图像': None,
                    '匹配数量': 0,
                    '匹配结果': []
                }
            
            if template_data is None:
                self.log_error("❌ 未接收到模板数据")
                return {
                    '标注图像': None,
                    '匹配数量': 0,
                    '匹配结果': []
                }
            
            # Step 2: 验证模板数据格式
            if not isinstance(template_data, dict) or 'metadata' not in template_data:
                self.log_error("❌ 模板数据格式错误")
                return {
                    '标注图像': None,
                    '匹配数量': 0,
                    '匹配结果': []
                }
            
            # Step 3: 获取算法配置
            params = self._param_container.get_values_dict()
            selected_algorithm = params.get('algorithm', 'hu_moments').lower()
            template_algorithm = template_data['metadata'].get('algorithm', '')
            
            # 检查算法一致性
            if template_algorithm and template_algorithm != selected_algorithm:
                self.log_warning(f"⚠️ 模板算法({template_algorithm})与选择算法({selected_algorithm})不一致")
                self.log_info("🔄 已自动切换到模板算法")
                selected_algorithm = template_algorithm
            
            # 若选择Shape Context但不可用，自动降级
            if selected_algorithm == 'shape_context' and not self._check_shape_context_availability():
                self.log_warning("⚠️ Shape Context不可用，已自动切换到Hu矩算法")
                selected_algorithm = 'hu_moments'
            
            self.log_info(f"🔧 使用算法: {selected_algorithm}")
            
            # Step 4: 提取轮廓
            gray = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY) if len(input_image.shape) == 3 else input_image.copy()
            
            # 自动二值化
            if len(np.unique(gray)) > 2:
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                self.log_info("检测到非二值图像，已自动使用Otsu阈值二值化")
            else:
                binary = gray.copy()
            
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            self.log_info(f"📊 检测到 {len(contours)} 个轮廓")
            
            if not contours:
                self.log_warning("⚠️ 未检测到任何轮廓")
                return {
                    '标注图像': input_image.copy(),
                    '匹配数量': 0,
                    '匹配结果': []
                }
            
            # Step 5: 获取筛选参数
            similarity_threshold = float(params.get('similarity_threshold', 0.8))
            min_area = float(params.get('min_area', 0))
            max_area = float(params.get('max_area', 999999))
            max_results = int(params.get('max_results', 10))
            
            # Step 6: 逐个匹配
            match_results = []
            
            for contour in contours:
                # 面积过滤
                area = cv2.contourArea(contour)
                if area < min_area or area > max_area:
                    continue
                
                # 执行匹配
                if selected_algorithm == 'hu_moments':
                    similarity = self._match_hu_moments(template_data, contour)
                elif selected_algorithm == 'shape_context':
                    similarity = self._match_shape_context(template_data, contour)
                elif selected_algorithm == 'hausdorff':
                    similarity = self._match_hausdorff(template_data, contour)
                else:
                    self.log_error(f"❌ 未知的算法: {selected_algorithm}")
                    similarity = 0.0
                
                # 阈值过滤
                if similarity >= similarity_threshold:
                    bounding_rect = cv2.boundingRect(contour)
                    centroid = self._compute_centroid(contour)
                    perimeter = cv2.arcLength(contour, True)
                    
                    match_results.append({
                        'contour': contour,
                        'similarity': round(similarity, 4),
                        'bounding_rect': {
                            'x': int(bounding_rect[0]),
                            'y': int(bounding_rect[1]),
                            'w': int(bounding_rect[2]),
                            'h': int(bounding_rect[3])
                        },
                        'centroid': centroid,
                        'area': round(area, 2),
                        'perimeter': round(perimeter, 2)
                    })
            
            # Step 7: 结果排序和限制
            match_results.sort(key=lambda x: x['similarity'], reverse=True)
            match_results = match_results[:max_results]
            
            self.log_info(f"✅ 找到 {len(match_results)} 个匹配结果")
            
            # Step 8: 构建输出数据（移除contour字段，因为无法JSON序列化）
            output_matches = []
            for i, result in enumerate(match_results):
                output_match = {
                    'rank': i + 1,
                    'similarity': result['similarity'],
                    'bounding_rect': result['bounding_rect'],
                    'centroid': result['centroid'],
                    'area': result['area'],
                    'perimeter': result['perimeter']
                }
                output_matches.append(output_match)
            
            # Step 9: 绘制标注图像
            annotated_image = input_image.copy()
            
            draw_contours = params.get('draw_contours', True)
            draw_centroids = params.get('draw_centroids', True)
            annotate_similarity = params.get('annotate_similarity', True)
            
            for i, result in enumerate(match_results):
                rank = i + 1
                color = self._get_color_by_rank(rank)
                contour = result['contour']
                
                # 绘制轮廓
                if draw_contours:
                    thickness = 3 if rank == 1 else 2
                    cv2.drawContours(annotated_image, [contour], -1, color, thickness)
                
                # 绘制质心
                if draw_centroids:
                    centroid = result['centroid']
                    cx, cy = int(centroid['x']), int(centroid['y'])
                    cv2.circle(annotated_image, (cx, cy), 5, color, -1)
                    
                    # 绘制排名标识
                    if rank == 1:
                        # 第1名添加金色星标
                        cv2.putText(annotated_image, "⭐", (cx - 10, cy - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 215, 255), 2)
                    elif rank <= 3:
                        # 第2-3名添加银色星标
                        cv2.putText(annotated_image, "☆", (cx - 10, cy - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (192, 192, 192), 2)
                
                # 标注相似度
                if annotate_similarity:
                    centroid = result['centroid']
                    cx, cy = int(centroid['x']), int(centroid['y'])
                    text = f"{result['similarity']:.2f}"
                    
                    # 白色文字 + 黑色描边
                    cv2.putText(annotated_image, text, (cx + 10, cy),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                    cv2.putText(annotated_image, text, (cx + 10, cy),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            self.log_success(f"✅ 模板匹配完成 (算法={selected_algorithm}, 匹配数={len(match_results)})")
            
            return {
                '标注图像': annotated_image,
                '匹配数量': len(match_results),
                '匹配结果': output_matches
            }
        
        except Exception as e:
            self.log_error(f"❌ 模板匹配错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                '标注图像': None,
                '匹配数量': 0,
                '匹配结果': []
            }
