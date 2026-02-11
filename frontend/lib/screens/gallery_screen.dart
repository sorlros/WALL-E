import 'package:flutter/material.dart';

class GalleryScreen extends StatelessWidget {
  const GalleryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF101622), // background-dark
      appBar: AppBar(
        backgroundColor: const Color(0xFF101622),
        elevation: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            Text(
              '균열 감지 갤러리',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 2),
            Text(
              '활성 미션 3개 • 이상 감지 142건',
              style: TextStyle(color: Colors.grey, fontSize: 12),
            ),
          ],
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            decoration: const BoxDecoration(
              color: Color(0xFF1A2332),
              shape: BoxShape.circle,
            ),
            child: IconButton(
              icon: const Icon(Icons.search, color: Colors.white70),
              onPressed: () {},
            ),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(50),
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                _buildFilterChip('전체 미션', isSelected: true),
                _buildFilterChip('오늘'),
                _buildFilterChip('높은 신뢰도'),
                _buildFilterChip('위치'),
              ],
            ),
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionHeader('미션 알파-04', '10월 24일 • 12개 항목'),
            const SizedBox(height: 12),
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 0.8,
              children: [
                _buildImageCard(
                  'https://lh3.googleusercontent.com/aida-public/AB6AXuAaLhCZTbFVnvXCF0QDSudRwb2MhB2HwyIqqYafSLK_IgIwGzB_QTESc-P-_ApBbIm-EMYrR1F1gqulzeI1By2hwHjOVua_N9X0q2xJmPkmC_doAe36X-RhXdLREizK9l8V4MM20ZQmIjThy0Lfrj3TjYUA9Ur5SpQRpg19dsQiD5b_VgTwAjIAux_mfr5Dc2zhl2e25kJ4Krk42cw9B4pFUBpDsj3XqyrekUD3kq34hhWs_DgH113icksqY__S4ZEzVIVRtH7LyK0',
                  '99% 위험',
                  Colors.red,
                  '섹터 4-N',
                  '#8392',
                ),
                _buildImageCard(
                  'https://lh3.googleusercontent.com/aida-public/AB6AXuCyYgNZH7-Lu4jctaizIJeZusaWnDpGYv5o_h6Zhir7qt3XKkbT9NhcvIkThHGayYURfnZLiLc68RdaeAB7Y1hbGGVTSwI47qcTLtd0lTkFLLC3qTWlroQCAAOBuXS2kdW2KEnOQ7LkB9lWhPIJRiF-sUHS8katRlyA5vP8QkQ-NZkQ99B2TeG_I262xq0MgFIeaW6K_3cGy2Ewwbx7jiiW0FHXGtrRFRNU5Uwo1JjbwUXXZEpbuF0jtpOKnuSGBU8liOYbhkrrOEY',
                  '85% 높음',
                  Colors.blue,
                  '섹터 4-E',
                  '#8395',
                ),
                _buildImageCard(
                  'https://lh3.googleusercontent.com/aida-public/AB6AXuD3otblfNqsQxyJKWQTCYK_3EyRY27mKL8edIMIqm4LQTWlrPZUkAuLt4_pjU9gycaF-BJjyRUrLX6Tcwi_qdgf30lnW30Pvmyg3bWXoiGtrtF5WOVTUIARsz_y-HFHkQ1uH47Dcs8Ei0NQwS1BRCoOE0Hvx1kFjE5JN-SZeGEL1r7WEDAQRzqCvHjwPrdRXFTnowp3Og8Lbd2LOxGnUBtYWReie3TmS9OWErJyEVSAadbLuuqm-wiZygoHoybBdF2EejISu6-KUIA',
                  '92% 심각',
                  Colors.orange,
                  '옥상 데크',
                  '#8401',
                ),
              ],
            ),
            const SizedBox(height: 24),
            _buildSectionHeader('현장 B - 경계 구역', '10월 22일 • 8개 항목'),
            const SizedBox(height: 12),
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 0.8,
              children: [
                _buildImageCard(
                  'https://lh3.googleusercontent.com/aida-public/AB6AXuD2yBvnT6eicRE-MD2GDLVebFJAil3LOIEzMszcMZ5qTt-ymandCUKhcR2TMY9lcj8hD_a7FOtH_EXbw9n0Nnym61OMA8hfoW0uODE2WcXLrUGphXMVmPBP90zq3QopS087J-sU8MpmA50wBa7VlC651SLzdVs45WfGD9nypOO6wEzgX5Xu4wGrMQZlDXtm1tHMwrJjXPacipM3oFrQKEEX9vLWO24eUdeNiSYYe8pp5cQk8uCbPnDw5XoFfpfFeQwTyUbnDjZY5X0',
                  '95% 위험',
                  Colors.red,
                  '동쪽 윙',
                  '#7902',
                ),
              ],
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFF135BEC),
        onPressed: () {},
        child: const Icon(Icons.download, color: Colors.white),
      ),
    );
  }

  Widget _buildFilterChip(String label, {bool isSelected = false}) {
    return Container(
      margin: const EdgeInsets.only(right: 8),
      child: Chip(
        label: Text(label),
        backgroundColor: isSelected
            ? const Color(0xFF135BEC)
            : const Color(0xFF1A2332),
        labelStyle: TextStyle(color: isSelected ? Colors.white : Colors.grey),
        shape: StadiumBorder(
          side: BorderSide(
            color: isSelected ? Colors.transparent : Colors.white10,
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title, String subtitle) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            Container(
              width: 4,
              height: 20,
              decoration: BoxDecoration(
                color: const Color(0xFF135BEC),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(width: 8),
            Text(
              title,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        Text(
          subtitle,
          style: const TextStyle(
            color: Colors.grey,
            fontSize: 12,
            fontFamily: 'monospace',
          ),
        ),
      ],
    );
  }

  Widget _buildImageCard(
    String imageUrl,
    String tag,
    Color tagColor,
    String location,
    String id,
  ) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1A2332),
        borderRadius: BorderRadius.circular(12),
        image: DecorationImage(
          image: NetworkImage(imageUrl),
          fit: BoxFit.cover,
          colorFilter: ColorFilter.mode(
            Colors.black.withOpacity(0.2),
            BlendMode.darken,
          ),
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            top: 8,
            left: 8,
            right: 8,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: tagColor.withOpacity(0.9),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.white24),
                  ),
                  child: Text(
                    tag,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
          Positioned(
            bottom: 12,
            left: 12,
            right: 12,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(
                      Icons.gps_fixed,
                      color: Color(0xFF135BEC),
                      size: 10,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      location,
                      style: const TextStyle(
                        color: Color(0xFF135BEC),
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                Text(
                  'ID: $id',
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 10,
                    fontFamily: 'monospace',
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
