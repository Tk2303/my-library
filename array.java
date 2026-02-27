import java.util.Scanner;
public class array{
    public static void main(String args[]){
        Scanner sc=new Scanner(System.in);
        int n;
        System.out.println("enter array size");
        n=sc.nextInt();
        int ar[]=new int[n];
        System.out.println("Enter array elements");
        for(int i=0;i<n;i++){
            ar[i]=sc.nextInt();
        }
        for(int i=0;i<n;i++){
            System.out.println("Element at index "+i+" is: "+ar[i]);
        }
    }
}