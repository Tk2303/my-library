public class DiagonalSum {
    public static int calculateDiagonalSum(int[][] m) {
        int sumPrimary = 0;
        int sumSecondary = 0;

        for (int i = 0; i < m.length; i++) {
            sumPrimary += m[i][i];
            if (i != m.length - i - 1) {
                sumSecondary += m[i][m.length - i - 1];
            }
        }

        return (sumPrimary == sumSecondary) ? sumPrimary : -1;
    }

    public static void main(String[] args) {
        int[][] m = {
            {1, 2, 3},
            {4, 5, 6},
            {7, 8, 10}
        };
        System.out.println(calculateDiagonalSum(m));
    }
}
